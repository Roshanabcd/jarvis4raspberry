"""
Phase 2 Live Browser Verification — ChatGPT Pill Composer Bar
Verifies:
  - #estop-btn is visible and enabled (never clicked)
  - Pill composer exists in both #tab-home and #tab-chat
  - cc-send starts in waveform-mode, switches to send-mode on input
  - cc-think-btn toggles .active class
  - chat-send-btn starts in waveform-mode
  - Screenshots saved at 1440×900 and 1280×720
"""

import os
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

BASE_URL = "http://127.0.0.1:8000"
EVIDENCE_DIR = Path(__file__).parent.parent.parent / "docs" / "jarvis-ui" / "evidence" / "phase-2-composer"
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

VIEWPORTS = [
    {"name": "1440x900", "width": 1440, "height": 900},
    {"name": "1280x720", "width": 1280, "height": 720},
]


def run_verification(viewport: dict) -> list[str]:
    """Run all checks for a single viewport size. Returns list of errors."""
    name = viewport["name"]
    errors = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = browser.new_page(viewport={"width": viewport["width"], "height": viewport["height"]})

        try:
            page.goto(BASE_URL, wait_until="networkidle", timeout=15000)
        except Exception as e:
            errors.append(f"[{name}] Page load failed: {e}")
            browser.close()
            return errors

        # --- 1. E-stop button: visible & enabled, NEVER clicked ---
        try:
            estop = page.locator("#estop-btn")
            assert estop.is_visible(), "#estop-btn not visible"
            assert estop.is_enabled(), "#estop-btn not enabled"
            print(f"  [{name}] ✅ #estop-btn visible and enabled")
        except AssertionError as e:
            errors.append(f"[{name}] ESTOP: {e}")

        # --- 2. Home tab pill composer ---
        try:
            # Click home tab
            home_tab = page.locator("#tab-home-btn, [data-tab='home'], button:has-text('Home')")
            if home_tab.count() > 0:
                home_tab.first.click()
                page.wait_for_timeout(300)

            pill = page.locator("#cc-pill-composer")
            assert pill.is_visible(), "#cc-pill-composer not visible on home tab"
            print(f"  [{name}] ✅ #cc-pill-composer visible on home tab")

            send_btn = page.locator("#cc-send")
            classes = send_btn.get_attribute("class") or ""
            assert "waveform-mode" in classes, f"#cc-send should start waveform-mode, got: {classes}"
            print(f"  [{name}] ✅ #cc-send starts in waveform-mode")

            # Screenshot home pill (before typing)
            page.screenshot(path=str(EVIDENCE_DIR / f"{name}-home-pill-empty.png"))
            print(f"  [{name}] 📸 Saved home pill empty screenshot")

            # Type text → send btn should switch to send-mode
            msg_input = page.locator("#cc-message")
            msg_input.fill("hello jarvis")
            page.wait_for_timeout(200)
            classes_after = send_btn.get_attribute("class") or ""
            assert "send-mode" in classes_after, f"#cc-send should switch to send-mode after typing, got: {classes_after}"
            print(f"  [{name}] ✅ #cc-send switches to send-mode after typing")

            page.screenshot(path=str(EVIDENCE_DIR / f"{name}-home-pill-typing.png"))
            print(f"  [{name}] 📸 Saved home pill typing screenshot")

            # Clear input → back to waveform-mode
            msg_input.fill("")
            page.wait_for_timeout(200)

        except AssertionError as e:
            errors.append(f"[{name}] Home pill: {e}")
            page.screenshot(path=str(EVIDENCE_DIR / f"{name}-home-pill-ERROR.png"))

        # --- 3. Think button toggle ---
        try:
            think_btn = page.locator("#cc-think-btn")
            assert think_btn.is_visible(), "#cc-think-btn not visible"
            classes_before = think_btn.get_attribute("class") or ""
            think_btn.click()
            page.wait_for_timeout(200)
            classes_after = think_btn.get_attribute("class") or ""
            assert "active" in classes_after, f"#cc-think-btn should have .active after click, got: {classes_after}"
            print(f"  [{name}] ✅ #cc-think-btn toggles .active on click")
            # Toggle back off
            think_btn.click()
            page.wait_for_timeout(100)
        except AssertionError as e:
            errors.append(f"[{name}] Think btn: {e}")

        # --- 4. Chat tab pill composer ---
        try:
            chat_tab = page.locator("#tab-chat-btn, [data-tab='chat'], button:has-text('Chat')")
            if chat_tab.count() > 0:
                chat_tab.first.click()
                page.wait_for_timeout(400)

            chat_pill = page.locator("#chat-pill-composer")
            assert chat_pill.is_visible(), "#chat-pill-composer not visible on chat tab"
            print(f"  [{name}] ✅ #chat-pill-composer visible on chat tab")

            chat_send = page.locator("#chat-send-btn")
            chat_classes = chat_send.get_attribute("class") or ""
            assert "waveform-mode" in chat_classes, f"#chat-send-btn should start waveform-mode, got: {chat_classes}"
            print(f"  [{name}] ✅ #chat-send-btn starts in waveform-mode")

            page.screenshot(path=str(EVIDENCE_DIR / f"{name}-chat-pill.png"))
            print(f"  [{name}] 📸 Saved chat pill screenshot")

        except AssertionError as e:
            errors.append(f"[{name}] Chat pill: {e}")
            page.screenshot(path=str(EVIDENCE_DIR / f"{name}-chat-pill-ERROR.png"))

        browser.close()

    return errors


def main():
    print(f"\n{'='*60}")
    print("Phase 2 Live Browser Verification")
    print(f"Backend: {BASE_URL}")
    print(f"Evidence dir: {EVIDENCE_DIR}")
    print(f"{'='*60}\n")

    all_errors = []

    for vp in VIEWPORTS:
        print(f"\n--- Viewport: {vp['name']} ({vp['width']}x{vp['height']}) ---")
        errs = run_verification(vp)
        all_errors.extend(errs)
        for e in errs:
            print(f"  ❌ {e}")

    print(f"\n{'='*60}")
    if all_errors:
        print(f"❌ FAILED — {len(all_errors)} error(s):")
        for e in all_errors:
            print(f"  • {e}")
        sys.exit(1)
    else:
        screenshots = list(EVIDENCE_DIR.glob("*.png"))
        print(f"✅ ALL CHECKS PASSED — {len(screenshots)} screenshot(s) saved to:")
        print(f"   {EVIDENCE_DIR}")
        for s in sorted(screenshots):
            print(f"   • {s.name}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
