"""Voice Command Integration Adapter for JARVIS Module 43.

Integrates with an existing JARVIS voice assistant without building a competing voice engine.
Ignores speech originating from screen media (speaker_source != 'user_mic') and requires
unambiguous target + explicit authorization before launching repairs.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from modules.module_43_autonomous_screen_guardian.backend.models.database import ScreenGuardianDB


class VoiceCommandAdapter:
    def __init__(self, db: ScreenGuardianDB) -> None:
        self.db = db

    def handle_command(
        self,
        utterance: str,
        speaker_source: str = "user_mic",
        explicit_authorization: bool = False,
        target_error_id: Optional[str] = None,
        workspace_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        if speaker_source.strip().lower() != "user_mic":
            return {
                "accepted": False,
                "intent": "ignored_untrusted_audio",
                "response": "Ignored audio not originating from the authenticated user microphone.",
            }

        low = utterance.strip().lower()
        errors = self.db.list_errors(limit=5)
        repairs = self.db.list_repairs(limit=5)
        ocr = self.db.list_ocr_history(limit=1)

        if "what is on my screen" in low:
            latest = ocr[0] if ocr else None
            return {
                "accepted": True,
                "intent": "describe_screen",
                "response": f"Latest captured app: {latest['source_app']}. Snippet: {latest['extracted_text'][:220]}"
                if latest
                else "No screen frames have been captured in this session yet.",
            }

        if "read this error" in low or "explain the problem" in low:
            err = self.db.get_error(target_error_id) if target_error_id else (errors[0] if errors else None)
            if not err:
                return {"accepted": True, "intent": "explain_error", "response": "No active errors detected."}
            return {
                "accepted": True,
                "intent": "explain_error",
                "error_id": err["error_id"],
                "response": f"{err['title']} in {err['source_app']}: {err['likely_cause']} Suggested action: {err['suggested_action']}",
            }

        if "prepare a fix" in low or "fix this error" in low:
            err = self.db.get_error(target_error_id) if target_error_id else (errors[0] if errors else None)
            if not err:
                return {"accepted": True, "intent": "repair_request", "response": "No detected error available to fix."}
            if "fix this error" in low and (not explicit_authorization or not workspace_path):
                return {
                    "accepted": True,
                    "intent": "repair_requires_authorization",
                    "error_id": err["error_id"],
                    "requires_approval": True,
                    "response": "Explicit authorization and a target workspace path are required before launching a code repair.",
                }
            return {
                "accepted": True,
                "intent": "prepare_or_launch_repair",
                "error_id": err["error_id"],
                "workspace_path": workspace_path,
                "requires_approval": not explicit_authorization,
                "response": f"Prepared repair context for '{err['title']}'.",
            }

        if "repair progress" in low or "did the test pass" in low:
            rep = repairs[0] if repairs else None
            if not rep:
                return {"accepted": True, "intent": "repair_status", "response": "No repair jobs have been created yet."}
            passed = (rep.get("test_results") or {}).get("passed")
            return {
                "accepted": True,
                "intent": "repair_status",
                "repair_id": rep["repair_id"],
                "response": f"Repair {rep['repair_id']} status is '{rep['status']}' (outcome: {rep['outcome']}, tests_passed={passed}).",
            }

        if "stop the repair" in low:
            rep = repairs[0] if repairs else None
            return {
                "accepted": True,
                "intent": "cancel_repair",
                "repair_id": rep["repair_id"] if rep else None,
                "response": f"Cancellation requested for repair {rep['repair_id']}." if rep else "No active repair to stop.",
            }

        return {
            "accepted": True,
            "intent": "unknown",
            "response": "Supported Screen Guardian voice commands: what is on my screen, read this error, explain the problem, prepare a fix, fix this error, show repair progress, stop the repair, did the test pass.",
        }
