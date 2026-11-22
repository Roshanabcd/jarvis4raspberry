"""
Developer CLI Escalation Bridge for JARVIS OS.
Provides safe discovery of local AI developer CLIs (Google Antigravity 'agy' and Anthropic Claude 'claude'),
automated read-only system inspection, and strictly gated remediation with fresh per-action PIN authorization.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path
import re
import shutil
import subprocess
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("JARVIS.Developer.CliBridge")

_SECRET_PATTERN = re.compile(r"(?i)(api[_-]?key|token|password|secret|pin)(\s*[=:]\s*)[^\s,;]+")


def redact(value: Any) -> str:
    """Redact sensitive values like tokens, keys, and PINs."""
    return _SECRET_PATTERN.sub(r"\1\2[REDACTED]", str(value))


class DeveloperCliBridge:
    """Manages CLI discovery, read-only system diagnosis, and PIN-gated remediation."""

    def __init__(self, repo_root: Optional[Path] = None):
        self.repo_root = repo_root or Path("/home/roshan/.gemini/antigravity/scratch/jarvis-os")

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

    def detect_clis(self) -> Dict[str, Any]:
        """Detect installed local developer CLIs and their FreeLLMAPI connection readiness."""
        freellm = self.get_freellmapi_config()
        fl_ready = freellm["configured"] and freellm["reachable"]

        cli_specs = [
            ("antigravity", ["antigravity", "agy", "/home/roshan/.local/bin/agy"], ["--version"], "antigravity"),
            ("claude", ["claude", "/home/roshan/.local/bin/claude"], ["--version"], "anthropic"),
            ("codex", ["codex", "/home/roshan/.local/bin/codex"], ["--version"], "openai"),
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
                    res = subprocess.run([bin_path] + ver_cmd, capture_output=True, text=True, timeout=3, check=False)
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

        return {
            **detected,
            "primary": primary,
            "has_developer_cli": len(installed_list) > 0,
            "installed_clis": installed_list,
            "installed_count": len(installed_list),
            "freellmapi": freellm,
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
        if act == "unmute_audio":
            try:
                res = subprocess.run(["wpctl", "set-mute", "@DEFAULT_AUDIO_SINK@", "0"], timeout=2, check=False)
                return {
                    "status": "ok",
                    "action": "unmute_audio",
                    "message": "Default audio sink unmuted successfully.",
                }
            except Exception as e:
                return {"status": "error", "message": f"Failed to unmute: {e}"}

        elif act == "restart_core":
            try:
                res = subprocess.run(["systemctl", "--user", "restart", "jarvis-core"], timeout=5, check=False)
                return {
                    "status": "ok",
                    "action": "restart_core",
                    "message": "jarvis-core.service restarted successfully.",
                }
            except Exception as e:
                return {"status": "error", "message": f"Failed to restart service: {e}"}

        elif act in ("run_cli", "cli_fix", "propose_fix", "run_coding_task"):
            chosen_cli = cli.lower().strip()
            if chosen_cli == "auto":
                chosen_cli = clis.get("primary", "antigravity")
            if chosen_cli == "agy":
                chosen_cli = "antigravity"

            cli_cmd_map = {
                "antigravity": [clis.get("antigravity", {}).get("path") or "agy", "-p", prompt or "Diagnose repository and suggest fixes", "--sandbox"],
                "claude": [clis.get("claude", {}).get("path") or "claude", "-p", "--no-session-persistence", "--permission-mode", "dontAsk", prompt or "Diagnose repository and suggest fixes"],
                "codex": [clis.get("codex", {}).get("path") or "codex", "-p", prompt or "Diagnose repository and suggest fixes"],
                "hermes": [clis.get("hermes", {}).get("path") or "hermes", "-p", prompt or "Diagnose repository and suggest fixes"],
                "aider": [clis.get("aider", {}).get("path") or "aider", "--message", prompt or "Diagnose repository and suggest fixes", "--no-auto-commits"],
                "opencode": [clis.get("opencode", {}).get("path") or "opencode", "run", prompt or "Diagnose repository and suggest fixes"],
                "cline": [clis.get("cline", {}).get("path") or "cline", "-p", prompt or "Diagnose repository and suggest fixes"],
            }

            if chosen_cli in cli_cmd_map and clis.get(chosen_cli, {}).get("installed"):
                cmd = cli_cmd_map[chosen_cli]
            else:
                return {
                    "status": "error",
                    "code": "CLI_UNAVAILABLE",
                    "error": f"Requested CLI '{chosen_cli}' is not installed or available on this system.",
                    "message": f"Requested CLI '{chosen_cli}' is not installed or available on this system.",
                }

            try:
                env = self.get_agent_env(chosen_cli)
                proc = subprocess.run(
                    cmd,
                    cwd=str(self.repo_root),
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    check=False
                )
                stdout_clean = redact(proc.stdout.strip()[:4096])
                stderr_clean = redact(proc.stderr.strip()[:2048])
                output = stdout_clean or stderr_clean

                if proc.returncode == 0:
                    return {
                        "status": "ok",
                        "cli": chosen_cli,
                        "action": act,
                        "output": output,
                        "exit_code": 0,
                        "message": f"Executed task with {chosen_cli.title()} (Exit code: 0).",
                    }
                else:
                    return {
                        "status": "error",
                        "code": "CLI_ERROR",
                        "cli": chosen_cli,
                        "action": act,
                        "output": output,
                        "exit_code": proc.returncode,
                        "error": stderr_clean or stdout_clean or f"CLI exited with code {proc.returncode}",
                        "message": f"CLI {chosen_cli.title()} exited with code {proc.returncode}.",
                    }
            except subprocess.TimeoutExpired:
                return {
                    "status": "error",
                    "code": "TIMEOUT",
                    "cli": chosen_cli,
                    "action": act,
                    "error": f"Execution timed out after {timeout}s",
                    "message": f"CLI {chosen_cli.title()} execution timed out after {timeout}s.",
                }
            except Exception as e:
                return {
                    "status": "error",
                    "code": "EXECUTION_FAILED",
                    "cli": chosen_cli,
                    "action": act,
                    "error": str(e),
                    "message": f"CLI execution error: {e}",
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

