"""
JARVIS OS — Screen Intelligence & Semantic Element Resolver
Resolves user interaction targets using a strict preference order:
1. Semantic Accessible DOM (Playwright browser backend when active)
2. Window and application metadata (wmctrl, xprop, window titles)
3. Structured UI elements
4. Screenshot visual difference & OCR bounding boxes
5. Coordinate fallback
Includes candidate confidence scoring and ambiguity detection.
"""

from __future__ import annotations

import logging
import os
import re
import time
from typing import Any, Dict, List, Optional, Tuple

from tools.desktop.browser_backend import browser_backend
from tools.desktop.native_backend import native_backend
from tools.desktop.desktop_perception import desktop_perception

logger = logging.getLogger("JARVIS.ScreenIntelligence")


class ScreenIntelligence:
    """Intelligent UI element detector, grounder, and ambiguity assessor."""

    def __init__(self):
        self.last_detected_error: Optional[Dict[str, Any]] = None

    def resolve_target(self, query: str, context_hint: Optional[str] = None) -> Dict[str, Any]:
        """
        Locate a target element semantically.
        Returns:
            {
                "status": "ok" | "ambiguous" | "not_found",
                "backend": "browser" | "desktop" | "ocr",
                "element": {...},
                "candidates": [...],
                "ambiguity_warning": str | None
            }
        """
        q = query.lower().strip()
        q_clean = re.sub(r'\s+(button|icon|field|box|textbox|tab|control|item|area)$', '', q).strip()

        # Step 1: If browser backend is active, search semantic DOM first
        if browser_backend.is_running():
            dom = browser_backend.inspect_dom()
            if dom.get("status") == "ok":
                candidates = []
                for el in dom.get("elements", []):
                    if not el.get("visible", True):
                        continue

                    label = (el.get("label") or "").lower()
                    text = (el.get("text") or "").lower()
                    val = (el.get("value") or "").lower()
                    el_id = (el.get("id") or "").lower()
                    name = (el.get("name") or "").lower()

                    score = 0.0
                    # Exact matches on raw or clean query
                    if q in (label, text, val, el_id) or (q_clean and q_clean in (label, text, val, el_id)):
                        score = 1.0
                    elif (text and text in q) or (label and label in q):
                        score = 0.95
                    elif q in label or q in text or q in val or q in el_id or q in name:
                        score = 0.8
                    elif q_clean and (q_clean in label or q_clean in text or q_clean in val or q_clean in el_id):
                        score = 0.85
                    # Number/ordinal matches: e.g. "option 1" matching id "option1"
                    elif q.replace(" ", "") in el_id or q.replace(" ", "") in label.replace(" ", ""):
                        score = 0.95
                    # Ordinal mapping (first option -> option 1)
                    elif any(ord_w in q for ord_w in ["first", "1st"]) and ("option1" in el_id or "option 1" in label):
                        score = 0.95
                    elif any(ord_w in q for ord_w in ["second", "2nd"]) and ("option2" in el_id or "option 2" in label):
                        score = 0.95
                    elif any(ord_w in q for ord_w in ["third", "3rd"]) and ("option3" in el_id or "option 3" in label):
                        score = 0.95

                    if score >= 0.7:
                        candidates.append({**el, "match_score": score})

                # Check ambiguity
                if len(candidates) > 1:
                    # Filter to highest scores
                    max_score = max(c["match_score"] for c in candidates)
                    top_candidates = [c for c in candidates if c["match_score"] == max_score]

                    if len(top_candidates) > 1 and all(c.get("type") == top_candidates[0].get("type") for c in top_candidates):
                        names = [c.get("id") or c.get("text") or c.get("label") for c in top_candidates]
                        return {
                            "status": "ambiguous",
                            "backend": "browser",
                            "message": f"Multiple matching elements detected for '{query}': {names}. Please clarify your target.",
                            "candidates": top_candidates,
                        }

                    # Otherwise take best
                    best = top_candidates[0]
                    return {
                        "status": "ok",
                        "backend": "browser",
                        "element": best,
                        "candidates": candidates,
                    }
                elif len(candidates) == 1:
                    return {
                        "status": "ok",
                        "backend": "browser",
                        "element": candidates[0],
                        "candidates": candidates,
                    }

        # Step 2: Native desktop window & panel inspection
        act_win = desktop_perception.get_active_window()
        wins = desktop_perception.list_open_windows()

        # Check if query matches an open window or app
        for w in wins:
            title = (w.get("title") or "").lower()
            app = (w.get("app") or "").lower()
            if q == app or q in title or q in app:
                geom = w.get("geometry", {})
                return {
                    "status": "ok",
                    "backend": "desktop",
                    "element": {
                        "type": "window",
                        "id": w.get("id"),
                        "title": w.get("title"),
                        "app": w.get("app"),
                        "center": {
                            "x": geom.get("x", 0) + geom.get("width", 100) // 2,
                            "y": geom.get("y", 0) + geom.get("height", 100) // 2,
                        },
                        "bounding_box": geom,
                    },
                }

        # Step 3: Desktop layout / element detector fallback
        from tools.desktop.element_detector import element_detector
        elem = element_detector.find_element(query, act_win)
        if elem:
            return {
                "status": "ok",
                "backend": "desktop",
                "element": elem.to_dict(),
            }

        return {
            "status": "not_found",
            "backend": "none",
            "message": f"No interface element matching '{query}' could be located.",
            "candidates": [],
        }

    def inspect_screen(self, query: Optional[str] = None) -> Dict[str, Any]:
        """Comprehensive screen observation combining window metadata, browser DOM, and OCR text."""
        act_win = desktop_perception.get_active_window()
        open_wins = desktop_perception.list_open_windows()
        res = desktop_perception.get_screen_resolution()

        browser_info = None
        if browser_backend.is_running():
            dom = browser_backend.inspect_dom()
            if dom.get("status") == "ok":
                browser_info = {
                    "url": browser_backend.get_current_url(),
                    "title": dom.get("title", ""),
                    "element_count": len(dom.get("elements", [])),
                }

        # Ephemeral visual snapshot
        snap = desktop_perception.capture_fullscreen()

        # Optional OCR extraction if a specific textual question is asked
        ocr_text = ""
        filepath = snap.get("filepath")
        if filepath and os.path.exists(filepath):
            try:
                import pytesseract
                from PIL import Image
                ocr_text = pytesseract.image_to_string(Image.open(filepath)).strip()
            except Exception as e:
                logger.debug("OCR extraction skipped: %s", e)

        obs = {
            "status": "ok",
            "active_window": act_win,
            "resolution": res,
            "open_windows_count": len(open_wins),
            "browser": browser_info,
            "ocr_snippet": ocr_text[:300] if ocr_text else None,
            "full_ocr": ocr_text if len(ocr_text) < 2000 else ocr_text[:2000] + "...",
            "timestamp": snap.get("timestamp", 0),
        }
        self.last_observation = obs
        return obs

    def check_screen_errors(self) -> Dict[str, Any]:
        """Inspect visible browser DOM and desktop screenshot for errors, alerts, or exceptions."""
        import time
        errors_found: List[Dict[str, Any]] = []

        # 1. Inspect Browser DOM if active
        if browser_backend.is_running():
            try:
                dom = browser_backend.inspect_dom()
                if dom.get("status") == "ok":
                    for el in dom.get("elements", []):
                        el_id = (el.get("id") or "").lower()
                        text = (el.get("text") or "").strip()
                        label = (el.get("label") or "").strip()
                        content = f"{text} {label}".strip()
                        if not content:
                            continue

                        # Check for error banners or failure indications
                        if any(k in el_id for k in ["error", "alert-danger", "fail", "exception"]) or \
                           re.search(r'\b(?:error|exception|failed|fatal|critical)\b', content, re.I):
                            # Filter out false positives like "0 errors"
                            if not re.search(r'\b0\s+errors\b', content, re.I):
                                errors_found.append({
                                    "source": "browser_dom",
                                    "location": el.get("selector") or f"#{el.get('id')}",
                                    "error_text": content,
                                    "severity": "high",
                                })
            except Exception as e:
                logger.debug("Browser DOM error inspection error: %s", e)

        # 2. Inspect Desktop Window OCR
        snap = desktop_perception.capture_active_window()
        filepath = snap.get("filepath")
        if filepath and os.path.exists(filepath):
            try:
                import pytesseract
                from PIL import Image
                raw_ocr = pytesseract.image_to_string(Image.open(filepath), config="--psm 11")
                error_patterns = [
                    r'(?:Error|Exception|Traceback|Failed|CRITICAL|FATAL|SyntaxError|TypeError|ValueError|NameError|ImportError|AttributeError|ZeroDivisionError)[:\s]+([^\n\r]+)',
                    r'(?:HTTP\s+(?:404|500|502|503)[^\n\r]*)',
                    r'(?:Connection\s+Refused[^\n\r]*)',
                ]
                for pat in error_patterns:
                    matches = re.findall(pat, raw_ocr, re.I)
                    for m in matches:
                        err_line = m.strip() if isinstance(m, str) else m[0].strip()
                        if err_line and not any(e["error_text"] == err_line for e in errors_found):
                            errors_found.append({
                                "source": "desktop_ocr",
                                "location": snap.get("title", "Active Window"),
                                "error_text": err_line,
                                "severity": "high",
                            })
            except Exception as e:
                logger.debug("OCR error inspection error: %s", e)

        if errors_found:
            top_err = errors_found[0]
            self.last_detected_error = top_err
            return {
                "status": "ok",
                "error_found": True,
                "count": len(errors_found),
                "error": top_err["error_text"],
                "errors": errors_found,
                "message": f"Found {len(errors_found)} error(s) displayed on screen: '{top_err['error_text']}' in {top_err['location']}.",
                "timestamp": time.time(),
            }

        self.last_detected_error = None
        return {
            "status": "ok",
            "error_found": False,
            "count": 0,
            "message": "No errors are currently displayed on the screen or in the active application.",
            "timestamp": time.time(),
        }

    def inspect_screen_with_diagnosis(self) -> Dict[str, Any]:
        """Perform real-time desktop problem diagnosis: inspect open windows, active app, errors via OCR and DOM."""
        from tools.desktop.desktop_perception import desktop_perception

        obs = desktop_perception.observe_desktop()
        err_check = self.check_screen_errors()

        active_win = obs.get("active_window", {})
        open_wins = obs.get("open_windows", [])
        has_err = err_check.get("error_found", False)

        act_app = active_win.get("app", "desktop")
        act_title = active_win.get("title", "Desktop")

        if has_err:
            err_msg = err_check.get("error", "Unknown error")
            spoken_summary = f"Detected problem in {act_title}: {err_msg}."
            recommendation = "Check the application console, terminal tracebacks, or restart the failing service."
        else:
            spoken_summary = f"Screen is clear. You are viewing {act_app} ({act_title}). No errors found in {len(open_wins)} active windows."
            recommendation = "Everything is running smoothly. Ready for your next command."

        return {
            "status": "ok",
            "has_error": has_err,
            "active_window": active_win,
            "open_windows_count": len(open_wins),
            "open_windows": open_wins,
            "errors": err_check.get("errors", []),
            "spoken_summary": spoken_summary,
            "recommendation": recommendation,
            "thumbnail_url": obs.get("snapshot", {}).get("thumbnail_url"),
            "resolution": obs.get("resolution"),
            "timestamp": obs.get("timestamp", time.time()),
        }

    def explain_detected_error(self, error_text: Optional[str] = None) -> Dict[str, Any]:
        """Explain the likely root cause and remediation for the detected error."""
        err = error_text or (self.last_detected_error.get("error_text") if self.last_detected_error else None)
        if not err:
            return {
                "status": "ok",
                "has_error": False,
                "explanation": "No error is currently detected on your screen to explain. You can ask me to inspect your screen first.",
            }

        err_low = err.lower()
        cause = "An unhandled exception or application failure occurred."
        remediation = "Inspect the relevant code or service logs and apply a fix."

        if "zerodivision" in err_low or "division by zero" in err_low:
            cause = "The program attempted to divide a number by zero in an arithmetic operation."
            remediation = "Add a zero-check guard clause (e.g. `if b == 0: return 0.0`) before the division."
        elif "connection refused" in err_low:
            cause = "The application tried to connect to a local port or server daemon that is offline or not listening."
            remediation = "Verify that the backend service or listener is started and listening on the specified port."
        elif "404" in err_low or "not found" in err_low:
            cause = "The requested URL route or static resource path does not exist on the server."
            remediation = "Check the API endpoint route path and ensure the corresponding route handler is registered."
        elif "syntaxerror" in err_low:
            cause = "Python parser encountered invalid grammar or mismatched punctuation in the source code."
            remediation = "Check indentation, matching brackets/parentheses, or colon usage."
        elif "assertionerror" in err_low:
            cause = "A unit test assertion or invariant validation condition failed."
            remediation = "Inspect expected vs actual values in the test assertion."

        explanation = (
            f"🔍 **Error Analysis:**\n\n"
            f"- **Observed Error:** `{err}`\n"
            f"- **Likely Cause:** {cause}\n"
            f"- **Recommended Fix:** {remediation}\n\n"
            f"You can instruct me to fix it using your available coding agent."
        )

        return {
            "status": "ok",
            "has_error": True,
            "error": err,
            "explanation": explanation,
            "cause": cause,
            "remediation": remediation,
        }

    def inspect_screen(self, query: Optional[str] = None) -> Dict[str, Any]:
        """Inspect current screen on DISPLAY=:0: active window, wmctrl window list, problem/error detection, and target resolution."""
        diag = self.inspect_screen_with_diagnosis()
        active_win = diag.get("active_window", {})
        open_wins = diag.get("open_windows", [])
        act_title = active_win.get("title", "Desktop")
        act_app = active_win.get("app", "desktop")

        target_info = None
        if query and query.strip():
            target_info = self.resolve_target(query.strip())

        win_list_str = "\n".join([f"- {w.get('app', 'app')} ({w.get('title', 'untitled')}) [id: {w.get('id', '')}]" for w in open_wins[:10]])
        has_err = diag.get("has_error", False)

        desc = (
            f"🖥️ Screen Status on DISPLAY=:0:\n"
            f"• Active Window: {act_app} — \"{act_title}\"\n"
            f"• Open Windows ({len(open_wins)}):\n{win_list_str}\n"
            f"• Problem Detection: {'⚠️ Error visible: ' + diag.get('errors', [{}])[0].get('error_text', 'Unknown') if has_err else '✅ No errors detected'}\n"
            f"• Recommendation: {diag.get('recommendation')}"
        )
        if target_info and target_info.get("status") == "ok":
            el = target_info.get("element", {})
            desc += f"\n• Resolved Target for '{query}': {el.get('type', 'element')} at ({el.get('x', 0)}, {el.get('y', 0)})"

        return {
            **diag,
            "description": desc,
            "target_resolution": target_info,
        }

    def monitor_screen(self) -> Dict[str, Any]:
        """Continuous monitor screen status query."""
        return self.inspect_screen()


# Global singleton instance
screen_intelligence = ScreenIntelligence()

