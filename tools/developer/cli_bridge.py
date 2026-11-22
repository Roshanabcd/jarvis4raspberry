"""
Developer CLI Escalation Bridge for JARVIS OS.
Provides safe discovery of local AI developer CLIs (Google Antigravity 'agy' and Anthropic Claude 'claude'),
automated read-only system inspection, and strictly gated remediation with fresh per-action PIN authorization.
"""
from __future__ import annotations

import base64
import logging
import os
from pathlib import Path
import re
import shutil
import subprocess
import time
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("JARVIS.Developer.CliBridge")

_SECRET_PATTERN = re.compile(r"(?i)(api[_-]?key|\bkey\b|token|password|secret|pin)(\s*[=:]\s*)[^\s,;]+")


def redact(value: Any) -> str:
    """Redact sensitive values like tokens, keys, and PINs."""
    return _SECRET_PATTERN.sub(r"\1\2[REDACTED]", str(value))


def detect_requested_output_file(prompt: str) -> Optional[str]:
    """Extract requested destination file path from user prompt if present."""
    if not prompt:
        return None
    # 1. Full absolute or home paths: /path/to/file.ext or ~/path/to/file.ext
    m = re.search(r'(?:^|[\s"\'`])([/~][a-zA-Z0-9_\.\-/]+\.[a-zA-Z0-9]{2,5})', prompt)
    if m:
        return os.path.expanduser(m.group(1).strip())
    # 2. Key phrases like 'to Downloads/horse.jpg', 'save as horse.jpg', 'output to /tmp/x.png'
    m2 = re.search(r'(?:to|as|in|into|named|path|file)\s+([a-zA-Z0-9_\.\-/]+\.[a-zA-Z0-9]{2,5})', prompt, re.I)
    if m2:
        val = m2.group(1).strip()
        if val.startswith("Downloads/"):
            return str(Path.home() / val)
        elif not val.startswith("/") and not val.startswith("~"):
            return str(Path.home() / "Downloads" / val)
        return os.path.expanduser(val)
    return None


def is_image_task(prompt: str) -> bool:
    """Check if the user prompt is requesting image generation or rendering."""
    if not prompt:
        return False
    p = prompt.lower()
    img_ext = bool(re.search(r"\.(jpg|jpeg|png|webp|svg|gif|bmp)\b", p))
    img_word = bool(re.search(r"\b(image|picture|photo|drawing|illustration|sketch|wallpaper|render|landscape|portrait)\b", p))
    create_word = bool(re.search(r"\b(generate|create|make|draw|paint|render|save|produce|fetch)\b", p))
    return (img_word and create_word) or (img_ext and create_word) or (img_ext and img_word)


def is_soft_failure(
    output: str,
    exit_code: int = 0,
    target_file: Optional[str] = None,
) -> Tuple[bool, str]:
    """Detect whether execution failed even if exit_code is 0, including 429 quota exhaustion or missing target file."""
    if exit_code != 0:
        return True, f"Exit code {exit_code}"

    out_lower = (output or "").lower()

    # 1. Quota / Rate limit / Generation failure patterns
    quota_patterns = [
        "429",
        "resource_exhausted",
        "rate limit",
        "quota exceeded",
        "exceeded your current quota",
        "cannot be rendered",
        "failed to generate",
        "model is overloaded",
        "credit balance is too low",
        "insufficient quota",
        "out of quota",
        "capacity exceeded",
        "quota",
    ]
    for pat in quota_patterns:
        if pat in out_lower:
            return True, f"Quota/Provider failure marker: '{pat}'"

    # 2. Target file check
    if target_file:
        p = Path(os.path.expanduser(target_file))
        if not p.is_file():
            return True, f"Target output file '{target_file}' was not created on disk"
        try:
            if p.stat().st_size == 0:
                return True, f"Target output file '{target_file}' is empty (0 bytes) on disk"
        except Exception as e:
            return True, f"Could not inspect target file '{target_file}': {e}"

    return False, ""


class DeveloperCliBridge:
    """Manages CLI discovery, read-only system diagnosis, and PIN-gated remediation."""

    def __init__(self, repo_root: Optional[Path] = None):
        self.repo_root = repo_root or Path("/home/roshan/.gemini/antigravity/scratch/jarvis-os")
        self._clis_cache: Optional[Dict[str, Any]] = None
        self._clis_cache_time: float = 0.0

    def get_freellmapi_config(self) -> Dict[str, Any]:
        """Check FreeLLMAPI gateway status and model count without exposing secrets."""
        from ai.providers.credentials import usable_key
        gateway_url = os.getenv("FREELLMAPI_BASE_URL", "http://localhost:3001/v1").rstrip("/")
        gateway_key = os.getenv("FREELLMAPI_API_KEY", "").strip()
        if not gateway_key:
            try:
                from dotenv import load_dotenv
                env_file = self.repo_root / ".env"
                if env_file.exists():
                    load_dotenv(env_file)
                    gateway_url = os.getenv("FREELLMAPI_BASE_URL", "http://localhost:3001/v1").rstrip("/")
                    gateway_key = os.getenv("FREELLMAPI_API_KEY", "").strip()
            except Exception:
                pass
        configured = bool(usable_key(gateway_key))

        reachable = False
        model_count = 0
        models_sample: List[str] = []
        if configured:
            try:
                import requests
                res = requests.get(
                    f"{gateway_url}/models",
                    headers={"Authorization": f"Bearer {gateway_key}", "Accept": "application/json"},
                    timeout=2.0
                )
                if res.status_code == 200:
                    reachable = True
                    data = res.json()
                    raw = data.get("data", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
                    model_count = len(raw)
                    models_sample = [m.get("id") if isinstance(m, dict) else str(m) for m in raw[:6]]
            except Exception:
                reachable = False

        return {
            "gateway_url": gateway_url,
            "configured": configured,
            "reachable": reachable,
            "model_count": model_count,
            "active_model": os.getenv("FREELLMAPI_MODEL", "auto"),
            "models_sample": models_sample,
        }

    def get_agent_env(self, cli_name: str) -> Dict[str, str]:
        """Build runtime environment injecting FreeLLMAPI connection without writing secrets to disk."""
        env = os.environ.copy()
        gateway_url = os.getenv("FREELLMAPI_BASE_URL", "http://localhost:3001/v1").rstrip("/")
        gateway_key = os.getenv("FREELLMAPI_API_KEY", "").strip()
        if not gateway_key:
            try:
                from dotenv import load_dotenv
                env_file = self.repo_root / ".env"
                if env_file.exists():
                    load_dotenv(env_file)
                    gateway_url = os.getenv("FREELLMAPI_BASE_URL", "http://localhost:3001/v1").rstrip("/")
                    gateway_key = os.getenv("FREELLMAPI_API_KEY", "").strip()
            except Exception:
                pass

        if gateway_key:
            bare_gateway = gateway_url.replace("/v1", "")
            # Anthropic protocol (for Claude Code CLI)
            env["ANTHROPIC_BASE_URL"] = bare_gateway
            env["ANTHROPIC_AUTH_TOKEN"] = gateway_key
            env["ANTHROPIC_API_KEY"] = gateway_key
            env["CLAUDE_BASE_URL"] = bare_gateway

            # OpenAI protocol (for Codex, Hermes, Aider, OpenCode, Cline)
            env["OPENAI_BASE_URL"] = gateway_url
            env["OPENAI_API_BASE"] = gateway_url
            env["OPENAI_API_KEY"] = gateway_key
            env["CODEX_API_BASE"] = gateway_url
            env["CODEX_API_KEY"] = gateway_key
            env["FREELLMAPI_API_KEY"] = gateway_key
            env["FREELLMAPI_BASE_URL"] = gateway_url

        return env

    def detect_clis(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Detect installed local developer CLIs and their FreeLLMAPI connection readiness."""
        now = time.time()
        freellm = self.get_freellmapi_config()
        fl_ready = freellm["configured"] and freellm["reachable"]

        if not force_refresh and self._clis_cache is not None and (now - self._clis_cache_time) < 60.0:
            cached = dict(self._clis_cache)
            cached["freellmapi"] = freellm
            return cached

        cli_specs = [
            ("antigravity", ["antigravity", "agy", "/home/roshan/.local/bin/agy"], ["--version"], "antigravity"),
            ("claude", ["claude", "/home/roshan/.local/bin/claude"], ["--version"], "anthropic"),
            ("codex", ["codex", "/home/roshan/.local/bin/codex"], ["--version"], "openai"),
            ("copilot", ["copilot", "gh", "/home/roshan/.local/bin/copilot"], ["--version"], "openai"),
            ("hermes", ["hermes", "/home/roshan/.local/bin/hermes"], ["--version"], "openai"),
            ("aider", ["aider", "/home/roshan/.local/bin/aider"], ["--version"], "openai"),
            ("opencode", ["opencode", "/home/roshan/.npm-global/bin/opencode"], ["--version"], "openai"),
            ("cline", ["cline", "/home/roshan/.npm-global/bin/cline"], ["--version"], "openai"),
        ]

        detected: Dict[str, Any] = {}
        installed_list = []

        for name, candidate_bins, ver_cmd, wire in cli_specs:
            bin_path = None
            for cb in candidate_bins:
                resolved = shutil.which(cb) or (cb if Path(cb).is_file() and os.access(cb, os.X_OK) else None)
                if resolved:
                    bin_path = resolved
                    break

            info: Dict[str, Any] = {
                "installed": bool(bin_path),
                "path": bin_path,
                "version": None,
                "protocol": wire,
                "freellmapi_protocol": wire,
                "freellmapi_ready": bool(bin_path and fl_ready),
                "freellmapi_connected": bool(bin_path and fl_ready),
            }

            if bin_path:
                installed_list.append(name)
                try:
                    res = subprocess.run([bin_path] + ver_cmd, capture_output=True, text=True, timeout=6, check=False)
                    if res.returncode == 0:
                        info["version"] = res.stdout.strip().splitlines()[0]
                    else:
                        info["version"] = "available"
                except Exception:
                    info["version"] = "available"

            detected[name] = info

        if "antigravity" in detected:
            detected["agy"] = detected["antigravity"]

        # Select primary CLI
        primary = "antigravity" if detected["antigravity"]["installed"] else (
            "claude" if detected["claude"]["installed"] else (
                installed_list[0] if installed_list else "none"
            )
        )

        result = {
            **detected,
            "primary": primary,
            "has_developer_cli": len(installed_list) > 0,
            "installed_clis": installed_list,
            "installed_count": len(installed_list),
            "freellmapi": freellm,
        }
        self._clis_cache = result
        self._clis_cache_time = now
        return result

    def generate_image_via_freellmapi(
        self,
        prompt: str,
        target_file: Optional[str] = None,
        timeout: int = 60,
    ) -> Dict[str, Any]:
        """Generate image using FreeLLMAPI /v1/images/generations and write directly to disk."""
        import requests

        gateway_url = os.getenv("FREELLMAPI_BASE_URL", "http://localhost:3001/v1").rstrip("/")
        gateway_key = os.getenv("FREELLMAPI_API_KEY", "").strip()
        if not gateway_key:
            try:
                from dotenv import load_dotenv
                env_file = self.repo_root / ".env"
                if env_file.exists():
                    load_dotenv(env_file)
                    gateway_url = os.getenv("FREELLMAPI_BASE_URL", "http://localhost:3001/v1").rstrip("/")
                    gateway_key = os.getenv("FREELLMAPI_API_KEY", "").strip()
            except Exception:
                pass

        if not gateway_key:
            return {
                "status": "error",
                "code": "MISSING_KEY",
                "error": "FREELLMAPI_API_KEY is not configured.",
                "message": "FreeLLMAPI API key missing for image generation fallback.",
            }

        endpoint = f"{gateway_url}/images/generations"
        logger.info("Calling FreeLLMAPI image endpoint at %s", endpoint)

        payload = {"prompt": prompt}
        headers = {
            "Authorization": f"Bearer {gateway_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        try:
            resp = requests.post(endpoint, json=payload, headers=headers, timeout=timeout)
            if resp.status_code != 200:
                return {
                    "status": "error",
                    "code": "HTTP_ERROR",
                    "http_status": resp.status_code,
                    "error": f"FreeLLMAPI image endpoint returned HTTP {resp.status_code}: {resp.text[:300]}",
                    "message": f"FreeLLMAPI image generation HTTP {resp.status_code}",
                }

            data = resp.json()
            raw_data = data.get("data", []) if isinstance(data, dict) else []
            if not raw_data or not isinstance(raw_data, list):
                return {
                    "status": "error",
                    "code": "EMPTY_RESPONSE",
                    "error": "No image data returned from FreeLLMAPI image endpoint.",
                    "message": "Empty response from FreeLLMAPI image endpoint.",
                }

            first_item = raw_data[0]
            b64_str = first_item.get("b64_json")
            img_bytes: Optional[bytes] = None

            if b64_str:
                img_bytes = base64.b64decode(b64_str)
            elif first_item.get("url"):
                url = first_item["url"]
                img_resp = requests.get(url, timeout=timeout)
                if img_resp.status_code == 200:
                    img_bytes = img_resp.content

            if not img_bytes:
                return {
                    "status": "error",
                    "code": "NO_IMAGE_BYTES",
                    "error": "Could not extract image data from FreeLLMAPI response.",
                    "message": "Failed to decode image from FreeLLMAPI response.",
                }

            out_path = Path(os.path.expanduser(target_file)) if target_file else (self.repo_root / "generated_image.jpg")
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_bytes(img_bytes)

            size_bytes = out_path.stat().st_size
            if size_bytes == 0:
                return {
                    "status": "error",
                    "code": "ZERO_BYTE_FILE",
                    "error": f"Written image file {out_path} is 0 bytes.",
                    "message": "Image write resulted in 0-byte file.",
                }

            logger.info("Successfully saved generated image to %s (%d bytes)", out_path, size_bytes)
            return {
                "status": "ok",
                "provider": "freellmapi_images",
                "output_file": str(out_path),
                "size_bytes": size_bytes,
                "output": f"Image successfully generated via FreeLLMAPI and saved to {out_path} ({size_bytes} bytes).",
                "message": f"Image successfully generated via FreeLLMAPI and saved to {out_path}.",
            }
        except Exception as exc:
            logger.error("FreeLLMAPI image generation exception: %s", exc)
            return {
                "status": "error",
                "code": "EXCEPTION",
                "error": str(exc),
                "message": f"FreeLLMAPI image generation failed: {exc}",
            }

    def diagnose_system(self) -> Dict[str, Any]:
        """Run safe, read-only system inspection across services, audio, git, and processes."""
        diagnostics: Dict[str, Any] = {
            "services": {},
            "audio": {},
            "git": {},
            "clis": self.detect_clis(),
            "recommendations": [],
        }

        # 1. Systemd Services (checks system service or user service)
        for sname in ("jarvis-core", "jarvis-voice"):
            try:
                res = subprocess.run(
                    ["systemctl", "is-active", sname],
                    capture_output=True,
                    text=True,
                    timeout=2,
                    check=False,
                )
                active_str = res.stdout.strip()
                if active_str != "active":
                    user_env = os.environ.copy()
                    user_env.setdefault("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}")
                    res_user = subprocess.run(
                        ["systemctl", "--user", "is-active", sname],
                        capture_output=True,
                        text=True,
                        timeout=2,
                        check=False,
                        env=user_env,
                    )
                    if res_user.stdout.strip() == "active":
                        active_str = "active"
                    elif not active_str:
                        active_str = res_user.stdout.strip() or "inactive"

                diagnostics["services"][sname] = {
                    "active": active_str == "active",
                    "status": active_str,
                }
            except Exception as e:
                diagnostics["services"][sname] = {"active": False, "status": "unknown", "error": str(e)}

        # 2. PipeWire Audio Introspection
        try:
            from tools.media.audio_stream_manager import audio_stream_manager
            vol_info = audio_stream_manager.get_master_sink_volume()
            streams = audio_stream_manager.list_active_streams()
            media_streams = [
                s for s in streams
                if s.get("direction") == "playback" and s.get("active")
            ]
            diagnostics["audio"] = {
                "master_volume_pct": vol_info.get("volume_pct", 100),
                "master_muted": vol_info.get("muted", False),
                "active_playback_streams_count": len(media_streams),
                "playback_streams": [s.get("name") for s in media_streams],
            }
            if vol_info.get("muted"):
                diagnostics["recommendations"].append("Default audio sink is MUTED; unmute to restore sound.")
            if len(media_streams) == 0:
                diagnostics["recommendations"].append("No active playback stream detected in PipeWire.")
        except Exception as e:
            diagnostics["audio"] = {"error": str(e)}

        # 3. Git Status in Repository
        try:
            git_res = subprocess.run(
                ["git", "-C", str(self.repo_root), "status", "--porcelain"],
                capture_output=True,
                text=True,
                timeout=3,
                check=False,
            )
            branch_res = subprocess.run(
                ["git", "-C", str(self.repo_root), "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True,
                text=True,
                timeout=2,
                check=False,
            )
            branch = branch_res.stdout.strip() if branch_res.returncode == 0 else "unknown"
            modified = [line.strip() for line in git_res.stdout.splitlines() if line.strip()]
            diagnostics["git"] = {
                "branch": branch,
                "modified_files_count": len(modified),
                "clean": len(modified) == 0,
            }
        except Exception as e:
            diagnostics["git"] = {"error": str(e)}

        # 4. Formatted Markdown Report
        clis = diagnostics["clis"]
        fl = clis.get("freellmapi", {})
        fl_status_str = f"ONLINE ({fl.get('model_count', 0)} models available via `{fl.get('gateway_url')}`)" if fl.get("reachable") else "OFFLINE"

        report_lines = [
            "### 🛠️ Developer CLI & Gateway Auto-Inspection Report",
            "",
            "#### 1. FreeLLMAPI Local Gateway",
            f"- **Gateway Endpoint:** `{fl.get('gateway_url', 'http://localhost:3001/v1')}`",
            f"- **Status:** `{'🟢 ' + fl_status_str if fl.get('reachable') else '🔴 OFFLINE'}`",
            f"- **Credential Configured:** `{'YES (Masked)' if fl.get('configured') else 'NO'}`",
            f"- **Active Default Model:** `{fl.get('active_model', 'auto')}`",
            "",
            "#### 2. Detected Local Coding Agents",
        ]

        cli_labels = [
            ("antigravity", "Google Antigravity (`agy`)", "Antigravity"),
            ("claude", "Anthropic Claude Code (`claude`)", "Anthropic Messages"),
            ("codex", "OpenAI Codex CLI (`codex`)", "OpenAI Chat"),
            ("hermes", "Hermes Agent (`hermes`)", "OpenAI Chat"),
            ("aider", "Aider AI Pair Programmer (`aider`)", "OpenAI Chat"),
            ("opencode", "OpenCode (`opencode`)", "OpenAI Chat"),
            ("cline", "Cline Autonomous CLI (`cline`)", "OpenAI Chat"),
        ]

        for k, label, proto in cli_labels:
            info = clis.get(k, {})
            if info.get("installed"):
                conn_badge = "⚡ Connected to FreeLLMAPI" if info.get("freellmapi_connected") else "Standalone"
                report_lines.append(f"- **{label}:** ✅ Installed (`{info.get('version') or 'available'}`) · {conn_badge} via {proto}")
            else:
                report_lines.append(f"- **{label}:** ❌ Not detected")

        report_lines.extend([
            "",
            "#### 3. Service & Hardware Health",
            f"- **`jarvis-core.service`:** `{'ACTIVE' if diagnostics['services'].get('jarvis-core', {}).get('active') else 'INACTIVE'}`",
            f"- **`jarvis-voice.service`:** `{'ACTIVE (Single mic owner)' if diagnostics['services'].get('jarvis-voice', {}).get('active') else 'INACTIVE'}`",
            f"- **Audio Master Sink:** `{'MUTED ⚠️' if diagnostics['audio'].get('master_muted') else 'UNMUTED'}` (Volume: {diagnostics['audio'].get('master_volume_pct', 'N/A')}%)",
            f"- **Active Playback Streams:** {diagnostics['audio'].get('active_playback_streams_count', 0)} active",
            f"- **Git Repository:** Branch `{diagnostics['git'].get('branch')}` ({diagnostics['git'].get('modified_files_count', 0)} modified paths)",
        ])

        if diagnostics["recommendations"]:
            report_lines.extend(["", "#### 4. Recommended Actions:"])
            for rec in diagnostics["recommendations"]:
                report_lines.append(f"- {rec}")

        report_lines.extend([
            "",
            "> [!NOTE]",
            "> *All diagnostic checks above are read-only. Mutating repairs and coding executions require explicit user confirmation and administrator PIN verification.*"
        ])

        diagnostics["markdown_report"] = "\n".join(report_lines)
        return diagnostics

    def verify_authorization(self, pin: str) -> Tuple[bool, str]:
        """Verify administrator PIN before executing any mutating action."""
        if not pin or not str(pin).strip():
            return False, "Missing administrator PIN."

        try:
            from tools.identity.user_manager import user_manager
            pin_ok, pin_msg = user_manager.verify_admin_pin(str(pin).strip())
            return pin_ok, pin_msg
        except Exception as e:
            logger.error("PIN verification error: %s", e)
            return False, f"Authorization error: {e}"

    def execute_remediation(
        self,
        action: str,
        pin: str,
        cli: str = "auto",
        prompt: Optional[str] = None,
        timeout: int = 180,
    ) -> Dict[str, Any]:
        """Execute a gated remediation action after verifying administrator PIN."""
        # 1. Enforce strict PIN authorization
        auth_ok, auth_msg = self.verify_authorization(pin)
        if not auth_ok:
            return {
                "status": "error",
                "code": "AUTHENTICATION_FAILED",
                "error": f"Authorization denied: {auth_msg}",
                "message": f"Authorization denied: {auth_msg}. Mutating remediation requires fresh administrator PIN.",
            }

        act = action.lower().strip()
        clis = self.detect_clis()

        # 2. Handle built-in safe repair actions
        # 2. Handle built-in safe repair actions
        if act == "unmute_audio":
            try:
                res = subprocess.run(["wpctl", "set-mute", "@DEFAULT_AUDIO_SINK@", "0"], timeout=2, check=False)
                spoken = None
                try:
                    from apps.voice.task_announcer import announce_task_completion
                    spoken = announce_task_completion(
                        status="success",
                        action_or_name="unmute_audio",
                        output_summary="Default audio sink unmuted successfully."
                    )
                except Exception as ann_e:
                    logger.warning("Spoken announcement failed: %s", ann_e)

                return {
                    "status": "ok",
                    "action": "unmute_audio",
                    "message": "Default audio sink unmuted successfully.",
                    "spoken_announcement": spoken,
                }
            except Exception as e:
                return {"status": "error", "message": f"Failed to unmute: {e}"}

        elif act == "restart_core":
            try:
                res = subprocess.run(["systemctl", "--user", "restart", "jarvis-core"], timeout=5, check=False)
                spoken = None
                try:
                    from apps.voice.task_announcer import announce_task_completion
                    spoken = announce_task_completion(
                        status="success",
                        action_or_name="restart_core",
                        output_summary="jarvis-core service restarted successfully."
                    )
                except Exception as ann_e:
                    logger.warning("Spoken announcement failed: %s", ann_e)

                return {
                    "status": "ok",
                    "action": "restart_core",
                    "message": "jarvis-core.service restarted successfully.",
                    "spoken_announcement": spoken,
                }
            except Exception as e:
                return {"status": "error", "message": f"Failed to restart service: {e}"}

        elif act in ("run_cli", "cli_fix", "propose_fix", "run_coding_task"):
            target_file = detect_requested_output_file(prompt or "")
            is_image = is_image_task(prompt or "")
            failover_trace: List[Dict[str, Any]] = []

            chosen_cli = cli.lower().strip()
            if chosen_cli == "agy":
                chosen_cli = "antigravity"

            cli_cmd_map = {
                "antigravity": [clis.get("antigravity", {}).get("path") or "agy", "-p", prompt or "Diagnose repository and suggest fixes", "--sandbox"],
                "claude": [clis.get("claude", {}).get("path") or "claude", "-p", "--no-session-persistence", "--permission-mode", "dontAsk", prompt or "Diagnose repository and suggest fixes"],
                "codex": [clis.get("codex", {}).get("path") or "codex", "-p", prompt or "Diagnose repository and suggest fixes"],
                "copilot": [clis.get("copilot", {}).get("path") or "copilot", "suggest", prompt or "Diagnose repository and suggest fixes"],
                "hermes": [clis.get("hermes", {}).get("path") or "hermes", "-p", prompt or "Diagnose repository and suggest fixes"],
                "aider": [clis.get("aider", {}).get("path") or "aider", "--message", prompt or "Diagnose repository and suggest fixes", "--no-auto-commits"],
                "opencode": [clis.get("opencode", {}).get("path") or "opencode", "run", prompt or "Diagnose repository and suggest fixes"],
                "cline": [clis.get("cline", {}).get("path") or "cline", "-p", prompt or "Diagnose repository and suggest fixes"],
            }

            from apps.voice.task_announcer import announce_task_completion

            # Branch A: Image generation flow with automatic FreeLLMAPI fallback
            if is_image:
                first_cli = "antigravity" if chosen_cli == "auto" else chosen_cli
                if first_cli in cli_cmd_map and clis.get(first_cli, {}).get("installed"):
                    try:
                        logger.info("Attempting image task with primary CLI %s", first_cli)
                        env = self.get_agent_env(first_cli)
                        cmd = cli_cmd_map[first_cli]
                        proc = subprocess.run(
                            cmd,
                            cwd=str(self.repo_root),
                            env=env,
                            capture_output=True,
                            text=True,
                            timeout=timeout,
                            check=False,
                        )
                        stdout_clean = redact(proc.stdout.strip()[:4096])
                        stderr_clean = redact(proc.stderr.strip()[:2048])
                        output = stdout_clean or stderr_clean

                        failed, fail_reason = is_soft_failure(output, proc.returncode, target_file)
                        if not failed:
                            failover_trace.append({"step": first_cli, "status": "success", "file": target_file})
                            spoken = announce_task_completion(
                                status="success",
                                action_or_name=act,
                                output_file=target_file,
                                output_summary=output,
                                failover_trace=failover_trace,
                            )
                            return {
                                "status": "ok",
                                "cli": first_cli,
                                "action": act,
                                "output": output,
                                "exit_code": 0,
                                "output_file": target_file,
                                "failover_trace": failover_trace,
                                "spoken_announcement": spoken,
                                "message": f"Executed image generation task with {first_cli.title()}.",
                            }
                        else:
                            failover_trace.append({"step": first_cli, "status": "failed", "reason": fail_reason})
                            logger.warning("%s image generation soft-failed (%s). Failing over to FreeLLMAPI...", first_cli, fail_reason)
                    except Exception as e:
                        failover_trace.append({"step": first_cli, "status": "failed", "reason": str(e)})
                        logger.warning("%s execution error: %s. Failing over to FreeLLMAPI...", first_cli, e)
                else:
                    failover_trace.append({"step": first_cli, "status": "skipped", "reason": "not installed"})

                # Failover to FreeLLMAPI image endpoint
                logger.info("Executing image failover to FreeLLMAPI...")
                img_res = self.generate_image_via_freellmapi(prompt=prompt or "", target_file=target_file, timeout=min(timeout, 60))
                if img_res.get("status") == "ok":
                    saved_path = img_res.get("output_file")
                    failover_trace.append({"step": "freellmapi_images", "status": "success", "file": saved_path})
                    spoken = announce_task_completion(
                        status="success",
                        action_or_name=act,
                        output_file=saved_path,
                        output_summary=img_res.get("output"),
                        failover_trace=failover_trace,
                    )
                    return {
                        "status": "ok",
                        "cli": "freellmapi_images",
                        "action": act,
                        "output": img_res.get("output", ""),
                        "exit_code": 0,
                        "output_file": saved_path,
                        "failover_trace": failover_trace,
                        "spoken_announcement": spoken,
                        "message": f"Successfully generated image via FreeLLMAPI and saved to {saved_path}.",
                    }
                else:
                    failover_trace.append({"step": "freellmapi_images", "status": "failed", "reason": img_res.get("error", "Generation failed")})

                # If all image options failed
                spoken = announce_task_completion(
                    status="quota_exhausted",
                    action_or_name=act,
                    failover_trace=failover_trace,
                    error="model quota is exhausted",
                )
                return {
                    "status": "error",
                    "code": "QUOTA_EXHAUSTED",
                    "action": act,
                    "output": "[FAILED – QUOTA/PROVIDER UNAVAILABLE] Could not generate or save requested image file across Antigravity and FreeLLMAPI.",
                    "failover_trace": failover_trace,
                    "spoken_announcement": spoken,
                    "error": "Model quota exhausted or image provider unavailable across Antigravity and FreeLLMAPI.",
                    "message": "[FAILED – QUOTA/PROVIDER UNAVAILABLE] Model quota exhausted or image provider unavailable.",
                }

            # Branch B: Coding / General Remediations Failover Chain
            candidate_order = ["antigravity", "claude", "codex", "hermes", "aider", "opencode", "cline"]
            if chosen_cli != "auto" and chosen_cli in candidate_order:
                candidates = [chosen_cli] + [c for c in candidate_order if c != chosen_cli]
            else:
                candidates = candidate_order

            installed_candidates = [c for c in candidates if clis.get(c, {}).get("installed")]
            if not installed_candidates:
                return {
                    "status": "error",
                    "code": "CLI_UNAVAILABLE",
                    "error": "No developer coding CLIs are installed or available on this system.",
                    "message": "No developer coding CLIs are installed or available on this system.",
                }

            last_output = ""
            for c_name in installed_candidates:
                cmd = cli_cmd_map.get(c_name)
                if not cmd:
                    continue
                try:
                    logger.info("Executing remediation task via candidate CLI: %s", c_name)
                    env = self.get_agent_env(c_name)
                    proc = subprocess.run(
                        cmd,
                        cwd=str(self.repo_root),
                        env=env,
                        capture_output=True,
                        text=True,
                        timeout=timeout,
                        check=False,
                    )
                    stdout_clean = redact(proc.stdout.strip()[:4096])
                    stderr_clean = redact(proc.stderr.strip()[:2048])
                    output = stdout_clean or stderr_clean
                    last_output = output

                    failed, fail_reason = is_soft_failure(output, proc.returncode, target_file)
                    if not failed:
                        failover_trace.append({"step": c_name, "status": "success", "file": target_file})
                        spoken = announce_task_completion(
                            status="success",
                            action_or_name=act,
                            output_file=target_file,
                            output_summary=output,
                            failover_trace=failover_trace,
                        )
                        return {
                            "status": "ok",
                            "cli": c_name,
                            "action": act,
                            "output": output,
                            "exit_code": 0,
                            "output_file": target_file,
                            "failover_trace": failover_trace,
                            "spoken_announcement": spoken,
                            "message": f"Executed task with {c_name.title()} (Exit code: 0).",
                        }
                    else:
                        failover_trace.append({"step": c_name, "status": "failed", "reason": fail_reason})
                        logger.warning("CLI %s soft-failed (%s). Trying next candidate...", c_name, fail_reason)

                except subprocess.TimeoutExpired:
                    failover_trace.append({"step": c_name, "status": "failed", "reason": f"Timeout after {timeout}s"})
                    logger.warning("CLI %s timed out after %ds", c_name, timeout)
                except Exception as e:
                    failover_trace.append({"step": c_name, "status": "failed", "reason": str(e)})
                    logger.warning("CLI %s error: %s", c_name, e)

            # All candidate CLIs failed
            is_quota = any(
                "quota" in str(t.get("reason", "")).lower()
                or "429" in str(t.get("reason", "")).lower()
                or "resource_exhausted" in str(t.get("reason", "")).lower()
                for t in failover_trace
            )
            err_code = "QUOTA_EXHAUSTED" if is_quota else "CLI_ERROR"
            spoken = announce_task_completion(
                status="quota_exhausted" if is_quota else "error",
                action_or_name=act,
                failover_trace=failover_trace,
                error="model quota is exhausted" if is_quota else f"CLI execution failed across {len(failover_trace)} agents",
            )
            label = "[FAILED – QUOTA EXHAUSTED]" if is_quota else "[FAILED]"
            return {
                "status": "error",
                "code": err_code,
                "action": act,
                "output": last_output or f"Failed across all candidate CLIs: {', '.join(t['step'] for t in failover_trace)}",
                "failover_trace": failover_trace,
                "spoken_announcement": spoken,
                "error": f"Task failed across all attempted CLIs ({', '.join(t['step'] for t in failover_trace)}).",
                "message": f"{label} Task failed across all attempted CLIs.",
            }

        return {
            "status": "error",
            "code": "UNKNOWN_ACTION",
            "error": f"Unrecognized remediation action '{action}'.",
            "message": f"Unrecognized remediation action '{action}'.",
        }

    def run_diagnostic_cli(
        self,
        prompt: str,
        preferred_cli: str = "auto",
        timeout: int = 120,
    ) -> Dict[str, Any]:
        """Run safe, non-interactive diagnostic reasoning using agy (primary) or claude (fallback).
        
        Used for task escalation and deep troubleshooting fallback without requiring root privileges.
        """
        clis = self.detect_clis()
        clean_prompt = (prompt or "Diagnose system state and suggest resolution").strip()

        # Determine CLI order: primary first, fallback second
        order: List[Tuple[str, List[str]]] = []
        if preferred_cli in ("antigravity", "agy") or (preferred_cli == "auto" and clis.get("antigravity", {}).get("installed")):
            if clis.get("antigravity", {}).get("installed"):
                order.append(("antigravity", [clis["antigravity"]["path"], "-p", clean_prompt, "--sandbox"]))
            if clis.get("claude", {}).get("installed"):
                order.append(("claude", [clis["claude"]["path"], "-p", "--no-session-persistence", "--permission-mode", "dontAsk", clean_prompt]))
        elif preferred_cli == "claude" or (preferred_cli == "auto" and clis.get("claude", {}).get("installed")):
            if clis.get("claude", {}).get("installed"):
                order.append(("claude", [clis["claude"]["path"], "-p", "--no-session-persistence", "--permission-mode", "dontAsk", clean_prompt]))
            if clis.get("antigravity", {}).get("installed"):
                order.append(("antigravity", [clis["antigravity"]["path"], "-p", clean_prompt, "--sandbox"]))
        else:
            # Try whichever is installed
            if clis.get("antigravity", {}).get("installed"):
                order.append(("antigravity", [clis["antigravity"]["path"], "-p", clean_prompt, "--sandbox"]))
            if clis.get("claude", {}).get("installed"):
                order.append(("claude", [clis["claude"]["path"], "-p", "--no-session-persistence", "--permission-mode", "dontAsk", clean_prompt]))

        if not order:
            return {
                "status": "error",
                "code": "NO_CLI_AVAILABLE",
                "output": "",
                "message": "Neither Antigravity ('agy') nor Claude ('claude') CLI is installed.",
            }

        last_error = ""
        for cli_name, cmd in order:
            try:
                logger.info("Executing diagnostic CLI escalation via %s", cli_name)
                env = self.get_agent_env(cli_name)
                proc = subprocess.run(
                    cmd,
                    cwd=str(self.repo_root),
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    check=False,
                )
                raw_out = (proc.stdout or "").strip()
                if not raw_out and proc.stderr:
                    raw_out = proc.stderr.strip()

                if raw_out:
                    clean_output = redact(raw_out[:4096])
                    return {
                        "status": "ok" if proc.returncode == 0 else "error",
                        "cli": cli_name,
                        "output": clean_output,
                        "exit_code": proc.returncode,
                        "message": f"Diagnostic reasoning completed via {cli_name.title()}.",
                    }
                last_error = f"{cli_name} returned empty output (exit {proc.returncode})"
            except subprocess.TimeoutExpired:
                last_error = f"{cli_name} timed out after {timeout}s"
                logger.warning("Diagnostic CLI %s timed out", cli_name)
            except Exception as e:
                last_error = f"{cli_name} execution error: {e}"
                logger.warning("Diagnostic CLI %s failed: %s", cli_name, e)

        return {
            "status": "error",
            "code": "CLI_EXECUTION_FAILED",
            "output": "",
            "message": f"Diagnostic CLI escalation failed: {last_error}",
        }


developer_cli_bridge = DeveloperCliBridge()

