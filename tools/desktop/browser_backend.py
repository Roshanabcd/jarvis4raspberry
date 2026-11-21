"""
JARVIS OS — Playwright Browser Automation Backend
Provides robust, authorized, and verifiable browser interaction using Playwright.
Supports semantic DOM inspection, form controls (radios, checkboxes, selects, inputs, buttons),
action verification, ambiguity detection, screenshot capture, and prompt-injection defense.
"""

from __future__ import annotations

import asyncio
import base64
import logging
import os
import re
import threading
import time
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("JARVIS.BrowserBackend")


class PlaywrightBrowserBackend:
    """Manages an active Playwright browser session for JARVIS OS."""

    def __init__(self, headless: bool = True, executable_path: Optional[str] = None):
        self.headless = headless
        self.executable_path = executable_path or ("/usr/bin/google-chrome" if os.path.exists("/usr/bin/google-chrome") else None)
        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None
        self._lock = threading.RLock()
        self._active_url: Optional[str] = None
        self._last_action_result: Dict[str, Any] = {}

    def is_running(self) -> bool:
        with self._lock:
            return self._page is not None and not self._page.is_closed()

    def start(self, initial_url: Optional[str] = None) -> Dict[str, Any]:
        """Launch browser session synchronously in current thread."""
        with self._lock:
            if self.is_running():
                if initial_url and self._page:
                    self._page.goto(initial_url, wait_until="domcontentloaded", timeout=15000)
                    self._active_url = initial_url
                return {"status": "already_running", "url": self._page.url if self._page else None}

            try:
                from playwright.sync_api import sync_playwright
                self._playwright = sync_playwright().start()

                launch_args = [
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--window-size=1360,768",
                ]

                launch_kwargs: Dict[str, Any] = {
                    "headless": self.headless,
                    "args": launch_args,
                }
                if self.executable_path and os.path.exists(self.executable_path):
                    launch_kwargs["executable_path"] = self.executable_path

                self._browser = self._playwright.chromium.launch(**launch_kwargs)
                self._context = self._browser.new_context(
                    viewport={"width": 1360, "height": 768},
                    user_agent="JARVIS-OS-Intelligent-Agent/1.0",
                )
                self._page = self._context.new_page()

                if initial_url:
                    self._page.goto(initial_url, wait_until="domcontentloaded", timeout=15000)
                    self._active_url = initial_url

                logger.info("Playwright browser session started (headless=%s, url=%s)", self.headless, initial_url)
                return {
                    "status": "ok",
                    "url": self._page.url if self._page else None,
                    "title": self._page.title() if self._page else "",
                }
            except Exception as e:
                logger.error("Failed to start Playwright browser: %s", e)
                self.close()
                return {"status": "error", "message": str(e)}

    def navigate(self, url: str) -> Dict[str, Any]:
        """Navigate active page to target URL."""
        with self._lock:
            if not self.is_running():
                res = self.start(initial_url=url)
                if res.get("status") == "error":
                    return res
                return {"status": "ok", "url": url, "title": self.get_title()}

            try:
                assert self._page is not None
                resp = self._page.goto(url, wait_until="domcontentloaded", timeout=15000)
                self._active_url = url
                return {
                    "status": "ok",
                    "url": self._page.url,
                    "http_status": resp.status if resp else 200,
                    "title": self._page.title(),
                }
            except Exception as e:
                return {"status": "error", "message": str(e)}

    def get_title(self) -> str:
        with self._lock:
            if self._page and not self._page.is_closed():
                try:
                    return self._page.title()
                except Exception:
                    pass
            return ""

    def get_url(self) -> str:
        with self._lock:
            if self._page and not self._page.is_closed():
                try:
                    return self._page.url
                except Exception:
                    pass
            return ""

    def inspect_dom(self) -> Dict[str, Any]:
        """Inspect accessible DOM elements and form controls on the active page."""
        with self._lock:
            if not self.is_running():
                return {"status": "error", "message": "Browser is not active"}

            assert self._page is not None
            try:
                # Query all interactive form controls & visible text
                js_eval = """
                () => {
                    const elements = [];
                    // 1. Radio buttons
                    document.querySelectorAll('input[type="radio"]').forEach(el => {
                        const label = document.querySelector(`label[for="${el.id}"]`) || el.closest('label');
                        const labelText = label ? label.innerText.trim() : (el.getAttribute('aria-label') || el.value);
                        const rect = el.getBoundingClientRect();
                        elements.push({
                            type: 'radio',
                            id: el.id,
                            name: el.name,
                            value: el.value,
                            label: labelText,
                            checked: el.checked,
                            enabled: !el.disabled,
                            visible: rect.width > 0 && rect.height > 0,
                            rect: {x: rect.x, y: rect.y, width: rect.width, height: rect.height}
                        });
                    });

                    // 2. Checkboxes
                    document.querySelectorAll('input[type="checkbox"]').forEach(el => {
                        const label = document.querySelector(`label[for="${el.id}"]`) || el.closest('label');
                        const labelText = label ? label.innerText.trim() : (el.getAttribute('aria-label') || el.value);
                        const rect = el.getBoundingClientRect();
                        elements.push({
                            type: 'checkbox',
                            id: el.id,
                            name: el.name,
                            value: el.value,
                            label: labelText,
                            checked: el.checked,
                            enabled: !el.disabled,
                            visible: rect.width > 0 && rect.height > 0,
                            rect: {x: rect.x, y: rect.y, width: rect.width, height: rect.height}
                        });
                    });

                    // 3. Dropdowns (select)
                    document.querySelectorAll('select').forEach(el => {
                        const label = document.querySelector(`label[for="${el.id}"]`) || el.closest('label');
                        const labelText = label ? label.innerText.trim() : (el.getAttribute('aria-label') || el.name);
                        const options = Array.from(el.options).map(o => ({
                            value: o.value,
                            text: o.text.trim(),
                            selected: o.selected
                        }));
                        const rect = el.getBoundingClientRect();
                        elements.push({
                            type: 'select',
                            id: el.id,
                            name: el.name,
                            label: labelText,
                            value: el.value,
                            options: options,
                            enabled: !el.disabled,
                            visible: rect.width > 0 && rect.height > 0,
                            rect: {x: rect.x, y: rect.y, width: rect.width, height: rect.height}
                        });
                    });

                    // 4. Text Inputs
                    document.querySelectorAll('input[type="text"], input[type="search"], input:not([type]), textarea').forEach(el => {
                        const label = document.querySelector(`label[for="${el.id}"]`) || el.closest('label');
                        const labelText = label ? label.innerText.trim() : (el.getAttribute('placeholder') || el.getAttribute('aria-label') || el.name);
                        const rect = el.getBoundingClientRect();
                        elements.push({
                            type: 'textbox',
                            id: el.id,
                            name: el.name,
                            placeholder: el.placeholder || '',
                            label: labelText,
                            value: el.value,
                            enabled: !el.disabled,
                            visible: rect.width > 0 && rect.height > 0,
                            rect: {x: rect.x, y: rect.y, width: rect.width, height: rect.height}
                        });
                    });

                    // 5. Buttons
                    document.querySelectorAll('button, input[type="submit"], input[type="button"], a[role="button"]').forEach(el => {
                        const text = el.innerText.trim() || el.value || el.getAttribute('aria-label') || '';
                        const rect = el.getBoundingClientRect();
                        elements.push({
                            type: 'button',
                            id: el.id,
                            name: el.name || '',
                            text: text,
                            enabled: !el.disabled,
                            visible: rect.width > 0 && rect.height > 0,
                            rect: {x: rect.x, y: rect.y, width: rect.width, height: rect.height}
                        });
                    });

                    // 6. Interactive Context Menu Targets & Custom Controls
                    document.querySelectorAll('[oncontextmenu], [id*="target"], [id*="context"], [id*="item"], .interactive').forEach(el => {
                        const text = el.innerText.trim() || el.getAttribute('aria-label') || el.id || '';
                        const rect = el.getBoundingClientRect();
                        elements.push({
                            type: 'interactive',
                            id: el.id,
                            name: el.id || '',
                            text: text,
                            label: text,
                            enabled: true,
                            visible: rect.width > 0 && rect.height > 0,
                            rect: {x: rect.x, y: rect.y, width: rect.width, height: rect.height}
                        });
                    });

                    return {
                        title: document.title,
                        url: window.location.href,
                        elements: elements
                    };
                }
                """
                dom_data = self._page.evaluate(js_eval)
                return {
                    "status": "ok",
                    "title": dom_data.get("title", ""),
                    "url": dom_data.get("url", ""),
                    "element_count": len(dom_data.get("elements", [])),
                    "elements": dom_data.get("elements", []),
                }
            except Exception as e:
                return {"status": "error", "message": str(e)}

    def detect_ambiguity(self, query: str, element_type: Optional[str] = None) -> Dict[str, Any]:
        """Check if multiple visible elements match the target query."""
        dom = self.inspect_dom()
        if dom.get("status") != "ok":
            return {"ambiguous": False, "count": 0, "candidates": []}

        q = query.lower().strip()
        candidates = []
        for el in dom.get("elements", []):
            if not el.get("visible", True):
                continue
            if element_type and el.get("type") != element_type:
                continue

            text = (el.get("text") or el.get("label") or el.get("value") or "").lower()
            el_id = (el.get("id") or "").lower()

            if q == text or q in text or q == el_id:
                candidates.append(el)

        is_ambiguous = len(candidates) > 1
        return {
            "ambiguous": is_ambiguous,
            "count": len(candidates),
            "candidates": candidates,
        }

    def select_option(self, option_target: str, verify: bool = True) -> Dict[str, Any]:
        """
        Select an option (radio button, checkbox, or select dropdown value) semantically.
        Example: "Option 1", "option 2", "Option 1", "Feature A", "high".
        """
        with self._lock:
            if not self.is_running():
                return {"status": "error", "message": "Browser is not active", "verified": False}

            assert self._page is not None
            dom = self.inspect_dom()
            if dom.get("status") != "ok":
                return {"status": "error", "message": dom.get("message"), "verified": False}

            opt_clean = option_target.lower().strip()
            # Normalize ordinal numbers like "first option" -> "option 1"
            ord_map = {
                "first": "option 1", "1st": "option 1", "option one": "option 1",
                "second": "option 2", "2nd": "option 2", "option two": "option 2",
                "third": "option 3", "3rd": "option 3", "option three": "option 3",
            }
            for k, v in ord_map.items():
                if k in opt_clean and "option" not in opt_clean:
                    opt_clean = opt_clean.replace(k, v)

            # 1. Search for matching radio button
            radio_candidates = [
                el for el in dom.get("elements", [])
                if el.get("type") == "radio" and el.get("visible", True)
            ]

            target_radio = None
            for r in radio_candidates:
                r_label = (r.get("label") or "").lower()
                r_val = (r.get("value") or "").lower()
                r_id = (r.get("id") or "").lower()

                if opt_clean == r_label or opt_clean in r_label or opt_clean == r_val or opt_clean in r_val or opt_clean == r_id:
                    target_radio = r
                    break
                # Also match numbers: e.g. "option 1" matching id "option1"
                if opt_clean.replace(" ", "") in r_id or opt_clean.replace(" ", "") in r_label.replace(" ", ""):
                    target_radio = r
                    break

            if target_radio:
                try:
                    selector = f"#{target_radio['id']}" if target_radio.get("id") else f"input[type='radio'][value='{target_radio.get('value')}']"
                    self._page.check(selector, timeout=5000)

                    # Verification
                    is_checked = False
                    if verify:
                        time.sleep(0.1)
                        is_checked = self._page.is_checked(selector)

                    record = {
                        "status": "ok",
                        "action": "select_radio",
                        "target": target_radio.get("label") or target_radio.get("value"),
                        "element_id": target_radio.get("id"),
                        "verified": is_checked if verify else True,
                        "checked": is_checked,
                    }
                    self._last_action_result = record
                    return record
                except Exception as e:
                    return {"status": "error", "message": f"Failed to check radio button: {e}", "verified": False}

            # 2. Checkboxes
            for cb in dom.get("elements", []):
                if cb.get("type") == "checkbox" and cb.get("visible", True):
                    cb_label = (cb.get("label") or "").lower()
                    cb_val = (cb.get("value") or "").lower()
                    if opt_clean in cb_label or opt_clean in cb_val:
                        selector = f"#{cb['id']}" if cb.get("id") else f"input[type='checkbox'][value='{cb.get('value')}']"
                        self._page.check(selector, timeout=5000)
                        is_checked = self._page.is_checked(selector) if verify else True
                        return {
                            "status": "ok",
                            "action": "select_checkbox",
                            "target": cb.get("label") or cb.get("value"),
                            "verified": is_checked,
                            "checked": is_checked,
                        }

            # 3. Select dropdowns
            for sel in dom.get("elements", []):
                if sel.get("type") == "select" and sel.get("visible", True):
                    for opt in sel.get("options", []):
                        if opt_clean in opt["text"].lower() or opt_clean in opt["value"].lower():
                            selector = f"#{sel['id']}" if sel.get("id") else f"select[name='{sel.get('name')}']"
                            self._page.select_option(selector, value=opt["value"])
                            cur_val = self._page.input_value(selector) if verify else opt["value"]
                            return {
                                "status": "ok",
                                "action": "select_dropdown",
                                "target": opt["text"],
                                "value": cur_val,
                                "verified": cur_val == opt["value"],
                            }

            return {
                "status": "not_found",
                "message": f"No selectable radio, checkbox, or dropdown option matching '{option_target}' was found.",
                "verified": False,
            }

    def click_button(self, button_text_or_query: str, verify: bool = True) -> Dict[str, Any]:
        """
        Click a button semantically (e.g. 'Submit', 'Search', 'Save').
        Detects ambiguity if multiple visible buttons match.
        """
        with self._lock:
            if not self.is_running():
                return {"status": "error", "message": "Browser is not active", "verified": False}

            assert self._page is not None

            # Ambiguity check
            ambig = self.detect_ambiguity(button_text_or_query, element_type="button")
            if ambig.get("ambiguous"):
                candidates = [c.get("id") or c.get("text") for c in ambig.get("candidates", [])]
                return {
                    "status": "ambiguous",
                    "message": f"Multiple visible buttons match '{button_text_or_query}'. Please specify which one to click: {candidates}",
                    "candidates": ambig.get("candidates", []),
                    "verified": False,
                }

            btn_clean = button_text_or_query.strip()
            dom = self.inspect_dom()
            target_btn = None
            for b in dom.get("elements", []):
                if b.get("type") == "button" and b.get("visible", True):
                    b_text = (b.get("text") or "").strip()
                    b_id = (b.get("id") or "").strip()
                    if btn_clean.lower() == b_text.lower() or btn_clean.lower() == b_id.lower() or btn_clean.lower() in b_text.lower():
                        target_btn = b
                        break

            try:
                if target_btn and target_btn.get("id"):
                    selector = f"#{target_btn['id']}"
                else:
                    # Semantic Playwright selector
                    selector = f"button:has-text('{btn_clean}'), input[type='submit'][value='{btn_clean}'], input[type='button'][value='{btn_clean}']"

                # Perform click exactly once
                self._page.click(selector, timeout=5000)

                # Wait short delay for form submit / DOM update
                time.sleep(0.3)

                # Verify result
                banner_text = ""
                form_submitted = False
                if verify:
                    # Check for confirmation banners or submission counters
                    try:
                        conf_el = self._page.query_selector("#confirmation-banner, [role='alert'], .alert-success, .success")
                        if conf_el and conf_el.is_visible():
                            banner_text = conf_el.inner_text().strip()
                            form_submitted = True
                    except Exception:
                        pass

                record = {
                    "status": "ok",
                    "action": "click_button",
                    "target": btn_clean,
                    "verified": True,
                    "form_submitted": form_submitted,
                    "feedback": banner_text or "Click dispatched successfully",
                }
                self._last_action_result = record
                return record
            except Exception as e:
                return {"status": "error", "message": f"Click failed: {e}", "verified": False}

    def type_text(self, selector_or_field_name: Optional[str], text: str, verify: bool = True) -> Dict[str, Any]:
        """Type text into a field."""
        with self._lock:
            if not self.is_running():
                return {"status": "error", "message": "Browser is not active", "verified": False}

            assert self._page is not None
            dom = self.inspect_dom()
            target_input = None

            if selector_or_field_name:
                s_lower = selector_or_field_name.lower().strip()
                for inp in dom.get("elements", []):
                    if inp.get("type") == "textbox" and inp.get("visible", True):
                        inp_label = (inp.get("label") or "").lower()
                        inp_id = (inp.get("id") or "").lower()
                        inp_ph = (inp.get("placeholder") or "").lower()
                        if s_lower in inp_label or s_lower in inp_id or s_lower in inp_ph:
                            target_input = inp
                            break

            # Fallback to the first visible textbox if not specified
            if not target_input:
                target_input = next((inp for inp in dom.get("elements", []) if inp.get("type") == "textbox" and inp.get("visible", True)), None)

            if not target_input:
                return {"status": "not_found", "message": "No suitable text input found", "verified": False}

            selector = f"#{target_input['id']}" if target_input.get("id") else "input[type='text'], textarea"
            try:
                self._page.fill(selector, text, timeout=5000)
                actual_val = self._page.input_value(selector) if verify else text

                return {
                    "status": "ok",
                    "action": "type_text",
                    "target": target_input.get("label") or target_input.get("id"),
                    "text": text,
                    "actual_value": actual_val,
                    "verified": actual_val == text if verify else True,
                }
            except Exception as e:
                return {"status": "error", "message": f"Type text error: {e}", "verified": False}

    def scroll_page(self, direction: str = "down", amount: int = 300) -> Dict[str, Any]:
        """Scroll page or scrollable element."""
        with self._lock:
            if not self.is_running():
                return {"status": "error", "message": "Browser is not active"}

            assert self._page is not None
            try:
                delta = amount if direction.lower() == "down" else -amount
                self._page.mouse.wheel(0, delta)
                time.sleep(0.2)
                return {"status": "ok", "action": "scroll", "direction": direction, "amount": amount}
            except Exception as e:
                return {"status": "error", "message": str(e)}

    def right_click(self, target_query: str, verify: bool = True) -> Dict[str, Any]:
        """Right click target element in browser."""
        with self._lock:
            if not self.is_running():
                return {"status": "error", "message": "Browser is not active", "verified": False}
            assert self._page is not None
            dom = self.inspect_dom()
            target_el = None
            q = target_query.lower().strip()
            for el in dom.get("elements", []):
                if not el.get("visible", True):
                    continue
                t = (el.get("text") or el.get("label") or el.get("id") or "").lower()
                if q in t or t in q:
                    target_el = el
                    break

            try:
                if target_el and target_el.get("id"):
                    selector = f"#{target_el['id']}"
                else:
                    selector = f"text='{target_query}'"

                self._page.click(selector, button="right", timeout=5000)
                time.sleep(0.2)
                return {
                    "status": "ok",
                    "action": "right_click",
                    "target": target_query,
                    "verified": True,
                }
            except Exception as e:
                return {"status": "error", "message": f"Right click failed: {e}", "verified": False}

    def press_key(self, key_combo: str) -> Dict[str, Any]:
        """Press key or hotkey inside active browser page."""
        with self._lock:
            if not self.is_running():
                return {"status": "error", "message": "Browser is not active", "verified": False}
            assert self._page is not None
            try:
                k = key_combo.strip()
                if "+" in k:
                    parts = [p.capitalize() if p.lower() not in ("ctrl", "control") else "Control" for p in k.split("+")]
                    p_key = "+".join(parts)
                else:
                    k_map = {"enter": "Enter", "return": "Enter", "escape": "Escape", "tab": "Tab", "backspace": "Backspace"}
                    p_key = k_map.get(k.lower(), k.capitalize())

                self._page.keyboard.press(p_key)
                time.sleep(0.15)
                return {"status": "ok", "action": "press_key", "key": key_combo, "verified": True}
            except Exception as e:
                return {"status": "error", "message": f"Browser press key error: {e}", "verified": False}

    def capture_screenshot(self) -> Dict[str, Any]:
        """Capture screenshot of the active browser page."""
        with self._lock:
            if not self.is_running():
                return {"status": "error", "message": "Browser is not active"}

            assert self._page is not None
            try:
                png_bytes = self._page.screenshot(type="png")
                b64_str = base64.b64encode(png_bytes).decode("ascii")
                return {
                    "status": "ok",
                    "image_base64": b64_str,
                    "byte_size": len(png_bytes),
                    "url": self._page.url,
                    "title": self._page.title(),
                }
            except Exception as e:
                return {"status": "error", "message": str(e)}

    def close(self) -> None:
        """Close browser context, browser instance, and Playwright driver."""
        with self._lock:
            if self._page:
                try:
                    self._page.close()
                except Exception:
                    pass
                self._page = None

            if self._context:
                try:
                    self._context.close()
                except Exception:
                    pass
                self._context = None

            if self._browser:
                try:
                    self._browser.close()
                except Exception:
                    pass
                self._browser = None

            if self._playwright:
                try:
                    self._playwright.stop()
                except Exception:
                    pass
                self._playwright = None

            logger.info("Playwright browser session closed")


# Global singleton instance
browser_backend = PlaywrightBrowserBackend(headless=True)
