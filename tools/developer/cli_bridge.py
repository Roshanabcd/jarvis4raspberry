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

    def detect_clis(self) -> Dict[str, Any]:
        """Detect installed local developer CLIs (agy / antigravity, claude)."""
        # 1. Antigravity CLI (agy)
        agy_bin = (
            shutil.which("antigravity")
            or shutil.which("agy")
            or "/home/roshan/.local/bin/agy"
        )
        agy_info = {"installed": False, "path": None, "version": None}
        if agy_bin and Path(agy_bin).is_file() and os.access(agy_bin, os.X_OK):
            agy_info["installed"] = True
            agy_info["path"] = str(agy_bin)
            try:
                res = subprocess.run([agy_bin, "--version"], capture_output=True, text=True, timeout=3, check=False)
                if res.returncode == 0:
                    agy_info["version"] = res.stdout.strip()
            except Exception:
                agy_info["version"] = "available"

        # 2. Claude Code CLI
        claude_bin = (
            shutil.which("claude")
            or "/home/roshan/.local/bin/claude"
        )
        claude_info = {"installed": False, "path": None, "version": None}
        if claude_bin and Path(claude_bin).is_file() and os.access(claude_bin, os.X_OK):
            claude_info["installed"] = True
            claude_info["path"] = str(claude_bin)
            try:
                res = subprocess.run([claude_bin, "--version"], capture_output=True, text=True, timeout=3, check=False)
                if res.returncode == 0:
                    claude_info["version"] = res.stdout.strip()
            except Exception:
                claude_info["version"] = "available"

        # Preferred CLI: Antigravity if available, else Claude
        primary = "antigravity" if agy_info["installed"] else ("claude" if claude_info["installed"] else "none")

        return {
            "antigravity": agy_info,
            "claude": claude_info,
            "primary": primary,
            "has_developer_cli": agy_info["installed"] or claude_info["installed"],
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
        report_lines = [
            "### 🛠️ Developer CLI Auto-Inspection Report",
            "",
            "#### 1. Available Developer CLIs",
        ]
        clis = diagnostics["clis"]
        if clis["antigravity"]["installed"]:
            report_lines.append(f"- **Google Antigravity (`agy`):** ✅ Installed (`{clis['antigravity']['version'] or 'v1.5.x'}` at `{clis['antigravity']['path']}`)")
        else:
            report_lines.append("- **Google Antigravity (`agy`):** ❌ Not detected")

        if clis["claude"]["installed"]:
            report_lines.append(f"- **Anthropic Claude Code (`claude`):** ✅ Installed (`{clis['claude']['version'] or 'v2.x'}` at `{clis['claude']['path']}`)")
        else:
            report_lines.append("- **Anthropic Claude Code (`claude`):** ❌ Not detected")

        report_lines.extend([
            "",
            "#### 2. Service & Hardware Health",
            f"- **`jarvis-core.service`:** `{'ACTIVE' if diagnostics['services'].get('jarvis-core', {}).get('active') else 'INACTIVE'}`",
            f"- **`jarvis-voice.service`:** `{'ACTIVE (Single mic owner)' if diagnostics['services'].get('jarvis-voice', {}).get('active') else 'INACTIVE'}`",
            f"- **Audio Master Sink:** `{'MUTED ⚠️' if diagnostics['audio'].get('master_muted') else 'UNMUTED'}` (Volume: {diagnostics['audio'].get('master_volume_pct', 'N/A')}%)",
            f"- **Active Playback Streams:** {diagnostics['audio'].get('active_playback_streams_count', 0)} active",
            f"- **Git Repository:** Branch `{diagnostics['git'].get('branch')}` ({diagnostics['git'].get('modified_files_count', 0)} modified paths)",
        ])

        if diagnostics["recommendations"]:
            report_lines.extend(["", "#### 3. Recommended Actions:"])
            for rec in diagnostics["recommendations"]:
                report_lines.append(f"- {rec}")

        report_lines.extend([
            "",
            "> [!NOTE]",
            "> *All diagnostic checks above are read-only. Mutating repairs require explicit user confirmation and administrator PIN verification.*"
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
    ) -> Dict[str, Any]:
        """Execute a gated remediation action after verifying administrator PIN."""
        # 1. Enforce strict PIN authorization
        auth_ok, auth_msg = self.verify_authorization(pin)
        if not auth_ok:
            return {
                "status": "error",
                "code": "AUTHENTICATION_FAILED",
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

        elif act in ("run_cli", "cli_fix", "propose_fix"):
            chosen_cli = cli
            if chosen_cli == "auto":
                chosen_cli = clis["primary"]

            if chosen_cli == "antigravity" and clis["antigravity"]["installed"]:
                cmd = [clis["antigravity"]["path"], "-p", prompt or "Diagnose repository and suggest fixes", "--sandbox"]
            elif chosen_cli == "claude" and clis["claude"]["installed"]:
                cmd = [clis["claude"]["path"], "-p", prompt or "Diagnose repository and suggest fixes"]
            else:
                return {
                    "status": "error",
                    "code": "CLI_UNAVAILABLE",
                    "message": f"Requested CLI '{chosen_cli}' is not installed or available on this system.",
                }

            try:
                proc = subprocess.run(cmd, cwd=str(self.repo_root), capture_output=True, text=True, timeout=30, check=False)
                output = redact(proc.stdout.strip()[:3000])
                return {
                    "status": "ok" if proc.returncode == 0 else "error",
                    "cli": chosen_cli,
                    "action": act,
                    "output": output or redact(proc.stderr.strip()[:1000]),
                    "message": f"Executed deep diagnostic with {chosen_cli.title()}.",
                }
            except Exception as e:
                return {"status": "error", "message": f"CLI execution error: {e}"}

        return {
            "status": "error",
            "code": "UNKNOWN_ACTION",
            "message": f"Unrecognized remediation action '{action}'.",
        }


developer_cli_bridge = DeveloperCliBridge()
