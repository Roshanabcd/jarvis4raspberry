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
import re
from typing import Any, Dict, List, Optional, Tuple

from tools.desktop.browser_backend import browser_backend
from tools.desktop.native_backend import native_backend
from tools.desktop.desktop_perception import desktop_perception

logger = logging.getLogger("JARVIS.ScreenIntelligence")


class ScreenIntelligence:
    """Intelligent UI element detector, grounder, and ambiguity assessor."""

    def __init__(self):
        pass

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


# Global singleton instance
screen_intelligence = ScreenIntelligence()
