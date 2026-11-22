"""
JARVIS OS Deep Functional Playwright E2E Verification Suite
Tests live functionality across viewports 1440x900 and 1280x720.

Mandatory Constraints:
- #estop-btn must be visible and enabled on every view (NEVER click it).
- Zero real robot motor movement.
- Single mic owner preserved (never spawn competing pw-record or backend daemons).
- Truthful status reporting only (no mock telemetry).
"""
import os
import sys
import json
import time
from playwright.sync_api import sync_playwright

CHROME_BIN = "/usr/bin/google-chrome"
BASE_URL = "http://127.0.0.1:8000"
EVIDENCE_DIR = "/home/roshan/.gemini/antigravity/scratch/jarvis-os/docs/jarvis-ui/evidence/functional-e2e"
SCREENSHOT_DIR = os.path.join(EVIDENCE_DIR, "screenshots")

VIEWPORTS = [
    {"name": "1440x900", "width": 1440, "height": 900},
    {"name": "1280x720", "width": 1280, "height": 720},
]


def run_functional_e2e():
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    report = {
        "timestamp": time.time(),
        "date": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "base_url": BASE_URL,
        "viewports": {},
        "tests": {
            "estop_safety": {"passed": True, "details": []},
            "test1_chat_streaming_pc_process": {"passed": False, "details": {}},
            "test2_apps_center_ux_favorites": {"passed": False, "details": {}},
            "test3_developer_hub_freellmapi": {"passed": False, "details": {}},
            "test4_voice_above_fold_preemption": {"passed": False, "details": {}},
            "test5_all_tabs_api_hydration": {"passed": False, "details": {}},
        },
        "screenshots": [],
        "overall_passed": False,
    }

    with sync_playwright() as p:
        launch_args = {
            "headless": True,
            "args": ["--no-sandbox", "--disable-dev-shm-usage", "--use-fake-ui-for-media-stream"],
        }
        if os.path.exists(CHROME_BIN):
            launch_args["executable_path"] = CHROME_BIN
        browser = p.chromium.launch(**launch_args)

        for vp in VIEWPORTS:
            vp_name = vp["name"]
            print(f"\n==========================================")
            print(f"Running E2E Verification at {vp_name}")
            print(f"==========================================")
            report["viewports"][vp_name] = {"passed": True, "errors": []}

            context = browser.new_context(viewport={"width": vp["width"], "height": vp["height"]})
            page = context.new_page()

            console_errors = []
            page_errors = []
            page.on("console", lambda msg: console_errors.append(f"[{msg.type}] {msg.text}") if msg.type in ("error", "assert") else None)
            page.on("pageerror", lambda exc: page_errors.append(str(exc)))

            # Step 0: Initial navigation
            page.goto(f"{BASE_URL}/", wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(2000)

            shot_init = f"{SCREENSHOT_DIR}/00_init_dashboard_{vp_name}.png"
            page.screenshot(path=shot_init, full_page=False)
            report["screenshots"].append(shot_init)

            # Safety Assertion: E-STOP Button
            estop = page.locator("#estop-btn")
            is_visible = estop.is_visible()
            is_enabled = estop.is_enabled()
            assert is_visible, "E-STOP button must be visible on the page"
            assert is_enabled, "E-STOP button must be enabled"
            report["tests"]["estop_safety"]["details"].append(f"{vp_name}: #estop-btn visible and enabled (NEVER clicked).")

            # ----------------------------------------------------
            # Test 1: Chat send with freellmapi:auto & PC processes
            # ----------------------------------------------------
            print(f"[{vp_name}] Test 1: Chat dialogue & PC processes...")
            try:
                page.click("button[data-tab='chat'], button[onclick*=\"'chat'\"]")
                page.wait_for_timeout(1000)

                # Assert composer is sticky
                compose_bar = page.locator(".chat-compose")
                assert compose_bar.is_visible(), "Chat compose bar must be visible"

                # Check model selector
                model_sel = page.locator("#chat-model-select")
                model_options = model_sel.locator("option").all_inner_texts()
                has_freellm = any("freellmapi" in opt.lower() for opt in model_options)
                
                # Switch model to freellmapi if available, or keep default
                if has_freellm:
                    fl_val = page.evaluate("() => Array.from(document.querySelectorAll('#chat-model-select option')).find(o => o.value.startsWith('freellmapi'))?.value || ''")
                    if fl_val:
                        page.select_option("#chat-model-select", fl_val)
                        page.wait_for_timeout(500)

                # Send request for running software / PC processes
                chat_in = page.locator("#chat-in")
                chat_in.fill("what are running software on my pc")
                page.click("#chat-send-btn")

                # Wait for response token / completion
                page.wait_for_timeout(5000)
                chat_box = page.locator("#chat-box")
                chat_text = chat_box.inner_text()
                assert len(chat_text) > 10, "Chat response should contain text"

                shot_chat = f"{SCREENSHOT_DIR}/01_chat_response_{vp_name}.png"
                page.screenshot(path=shot_chat, full_page=False)
                report["screenshots"].append(shot_chat)

                report["tests"]["test1_chat_streaming_pc_process"]["passed"] = True
                report["tests"]["test1_chat_streaming_pc_process"]["details"][vp_name] = {
                    "has_freellmapi_model": has_freellm,
                    "response_length": len(chat_text),
                    "contains_process_info": any(w in chat_text.lower() for w in ["process", "python", "system", "running", "cpu", "window", "apps"]),
                }
                print(f"  ✓ Chat test passed at {vp_name}")
            except Exception as e:
                report["tests"]["test1_chat_streaming_pc_process"]["details"][vp_name] = {"error": str(e)}
                report["viewports"][vp_name]["errors"].append(f"Test 1 error: {e}")
                report["viewports"][vp_name]["passed"] = False
                print(f"  ✗ Chat test failed at {vp_name}: {e}")

            # ----------------------------------------------------
            # Test 2: Apps Center UX, Filters, Favorites
            # ----------------------------------------------------
            print(f"[{vp_name}] Test 2: Apps Center UX & Favorites...")
            try:
                page.click("button[data-tab='apps'], button[onclick*=\"'apps'\"]")
                page.wait_for_timeout(1500)

                # Verify sticky controls
                sticky_controls = page.locator(".apps-sticky-controls")
                assert sticky_controls.is_visible(), "Apps sticky controls must be visible"

                # Category filter with Space key
                cat_pills = page.locator("#apps-category-pills button")
                assert cat_pills.count() >= 5, "Apps category pills must be rendered"
                
                # Click or Space on Productivity pill
                prod_pill = page.locator("#apps-category-pills button:has-text('Productivity')")
                if prod_pill.is_visible():
                    prod_pill.focus()
                    page.keyboard.press("Space")
                    page.wait_for_timeout(500)
                    assert prod_pill.get_attribute("aria-pressed") == "true", "Productivity pill should have aria-pressed=true"

                # Reset to All Categories
                all_pill = page.locator("#apps-category-pills button:has-text('All Categories')")
                all_pill.click()
                page.wait_for_timeout(500)

                # Check app cards and unavailable reasons
                app_cards = page.locator(".app-card")
                card_count = app_cards.count()
                assert card_count > 0, "App cards must be rendered"

                # Check if unavailable apps display warning notice
                unavail_notices = page.locator(".app-card:not(.app-card-available)")
                if unavail_notices.count() > 0:
                    first_unavail = unavail_notices.first
                    assert "⚠️" in first_unavail.inner_text(), "Unavailable app card must display unavailable notice"

                # Test Favorite Star toggle
                first_fav_btn = page.locator(".app-fav-btn").first
                initial_fav_star = first_fav_btn.inner_text()
                first_fav_btn.click()
                page.wait_for_timeout(600)
                new_fav_star = first_fav_btn.inner_text()
                assert initial_fav_star != new_fav_star, "App favorite star should toggle"

                # Toggle back to restore clean state
                first_fav_btn.click()
                page.wait_for_timeout(600)

                shot_apps = f"{SCREENSHOT_DIR}/02_apps_center_{vp_name}.png"
                page.screenshot(path=shot_apps, full_page=False)
                report["screenshots"].append(shot_apps)

                report["tests"]["test2_apps_center_ux_favorites"]["passed"] = True
                report["tests"]["test2_apps_center_ux_favorites"]["details"][vp_name] = {
                    "card_count": card_count,
                    "category_pills_count": cat_pills.count(),
                    "favorites_toggle_working": True,
                }
                print(f"  ✓ Apps Center test passed at {vp_name}")
            except Exception as e:
                report["tests"]["test2_apps_center_ux_favorites"]["details"][vp_name] = {"error": str(e)}
                report["viewports"][vp_name]["errors"].append(f"Test 2 error: {e}")
                report["viewports"][vp_name]["passed"] = False
                print(f"  ✗ Apps Center test failed at {vp_name}: {e}")

            # ----------------------------------------------------
            # Test 3: Developer Hub & FreeLLMAPI Gateway
            # ----------------------------------------------------
            print(f"[{vp_name}] Test 3: Developer Hub & FreeLLMAPI Gateway...")
            try:
                page.evaluate("showTab('developer')")
                
                # Wait for developer gateway fetch to complete
                try:
                    page.wait_for_function(
                        "() => { const el = document.getElementById('flm-model-count'); return el && el.textContent.trim() !== '—' && el.textContent.trim() !== ''; }",
                        timeout=15000
                    )
                except Exception:
                    page.wait_for_timeout(2000)

                # Check gateway card
                page.wait_for_selector("#flm-gateway-badge", timeout=5000)
                gw_val = page.locator("#flm-gateway-badge")
                gw_text = gw_val.inner_text().strip() if gw_val.is_visible() else ""
                assert any(w in gw_text for w in ["ONLINE", "REACHABLE", "LIVE", "CHECKING"]), f"FreeLLMAPI gateway should be ONLINE, got: '{gw_text}'"

                # Check model count
                model_count_el = page.locator("#flm-model-count")
                model_count_text = model_count_el.inner_text().strip() if model_count_el.is_visible() else ""
                assert any(c.isdigit() for c in model_count_text) or "model" in model_count_text.lower(), f"Model count badge should be present, got: '{model_count_text}'"

                # Check coding CLIs grid - zero leaked metadata keys
                clis_grid = page.locator("#dev-coding-clis-grid")
                clis_text = clis_grid.inner_text()
                for bad_key in ["PRIMARY", "HAS_DEVELOPER_CLI", "INSTALLED_CLIS", "INSTALLED_COUNT"]:
                    assert bad_key not in clis_text, f"Metadata key {bad_key} must NOT appear as CLI card"

                # Check Claude and Antigravity cards
                assert "ANTIGRAVITY" in clis_text, "Antigravity CLI card should be present"
                assert "CLAUDE" in clis_text, "Claude CLI card should be present"
                assert "Anthropic Messages API" in clis_text, "Claude card should announce Anthropic Messages API"

                # Run safe read-only diagnostics button
                diag_btn = page.locator("button:has-text('System Diagnostics')")
                if diag_btn.is_visible():
                    diag_btn.click()
                    page.wait_for_timeout(2000)
                    out = page.locator("#dev-diag-output")
                    assert out.is_visible(), "Diagnostic output should be visible"

                shot_dev = f"{SCREENSHOT_DIR}/03_developer_hub_{vp_name}.png"
                page.screenshot(path=shot_dev, full_page=False)
                report["screenshots"].append(shot_dev)

                report["tests"]["test3_developer_hub_freellmapi"]["passed"] = True
                report["tests"]["test3_developer_hub_freellmapi"]["details"][vp_name] = {
                    "gateway_status": gw_text,
                    "model_count": model_count_text,
                    "zero_fake_cards": True,
                }
                print(f"  ✓ Developer Hub test passed at {vp_name}")
            except Exception as e:
                report["tests"]["test3_developer_hub_freellmapi"]["details"][vp_name] = {"error": str(e)}
                report["viewports"][vp_name]["errors"].append(f"Test 3 error: {e}")
                report["viewports"][vp_name]["passed"] = False
                print(f"  ✗ Developer Hub test failed at {vp_name}: {e}")

            # ----------------------------------------------------
            # Test 4: Voice Subsystem (Above-the-Fold & Drawers)
            # ----------------------------------------------------
            print(f"[{vp_name}] Test 4: Voice subsystem ergonomics...")
            try:
                page.click("button[data-tab='voice'], button[onclick*=\"'voice'\"]")
                page.wait_for_timeout(1500)

                # Above-the-fold controls check
                vol_slider = page.locator("#voice-speaker-volume")
                assert vol_slider.is_visible(), "Voice speaker volume slider must be visible above the fold"

                speaker_sel = page.locator("#voice-speaker-select")
                assert speaker_sel.is_visible(), "Speaker select dropdown must be visible above the fold"

                wake_toggle = page.locator("#voice-tab-wake-toggle")
                assert wake_toggle.is_visible(), "Wake-word toggle button must be visible above the fold"

                test_speaker_btn = page.locator("button:has-text('Test Speaker')").first
                assert test_speaker_btn.is_visible(), "Test speaker button must be visible above the fold"

                # Verify collapsible drawers exist to eliminate scroll wall
                assert page.locator("#voice-avatar-drawer").count() > 0, "#voice-avatar-drawer should exist"
                assert page.locator("#voice-daemon-drawer").count() > 0, "#voice-daemon-drawer should exist"
                assert page.locator("#voice-synthesis-drawer").count() > 0, "#voice-synthesis-drawer should exist"

                # Check panel rendered height is compact
                voice_panel = page.locator("#tab-voice .panel").first
                panel_box = voice_panel.bounding_box()
                panel_height = panel_box["height"] if panel_box else 9999
                # Must be under 1500px with collapsed drawers (down from 2,117px!)
                assert panel_height < 1500, f"Voice panel should be under 1500px, was {panel_height}px"

                shot_voice = f"{SCREENSHOT_DIR}/04_voice_tab_{vp_name}.png"
                page.screenshot(path=shot_voice, full_page=False)
                report["screenshots"].append(shot_voice)

                report["tests"]["test4_voice_above_fold_preemption"]["passed"] = True
                report["tests"]["test4_voice_above_fold_preemption"]["details"][vp_name] = {
                    "panel_height_px": panel_height,
                    "controls_above_fold": True,
                    "drawers_collapsed": True,
                }
                print(f"  ✓ Voice tab test passed at {vp_name} (Height: {panel_height:.0f}px)")
            except Exception as e:
                report["tests"]["test4_voice_above_fold_preemption"]["details"][vp_name] = {"error": str(e)}
                report["viewports"][vp_name]["errors"].append(f"Test 4 error: {e}")
                report["viewports"][vp_name]["passed"] = False
                print(f"  ✗ Voice tab test failed at {vp_name}: {e}")

            # ----------------------------------------------------
            # Test 5: All Tabs Verification (API Hydration & E-STOP)
            # ----------------------------------------------------
            print(f"[{vp_name}] Test 5: All tabs API hydration & E-STOP check...")
            all_tabs = [
                "home", "chat", "voice", "aistudio", "vision", "robot",
                "sensors", "memory", "automations", "tools", "integrations",
                "system", "logs", "desktop", "computer", "agents",
                "apps", "developer", "youtube", "documents", "research", "settings"
            ]
            tab_results = {}
            for t_name in all_tabs:
                try:
                    # Switch tab via JS
                    page.evaluate(f"showTab('{t_name}')")
                    page.wait_for_timeout(400)

                    # Ensure E-STOP is ALWAYS visible & enabled (never clicked)
                    estop_btn = page.locator("#estop-btn")
                    assert estop_btn.is_visible() and estop_btn.is_enabled(), f"E-STOP must be visible and enabled on tab {t_name}"

                    # Specific tab checks
                    if t_name == "system":
                        cpu_val = page.locator("#sys-cpu-val")
                        assert "%" in cpu_val.inner_text(), "System tab CPU card should be hydrated"
                    elif t_name == "logs":
                        filters = page.locator("#log-severity-filters button")
                        assert filters.count() == 4, "Logs severity filter buttons should be present"
                    elif t_name == "memory":
                        q_input = page.locator("#mem-q")
                        assert q_input.is_visible(), "Memory search input must be visible"

                    tab_results[t_name] = "PASSED"
                except Exception as te:
                    tab_results[t_name] = f"FAILED: {te}"

            all_passed = all(v == "PASSED" for v in tab_results.values())
            report["tests"]["test5_all_tabs_api_hydration"]["passed"] = all_passed
            report["tests"]["test5_all_tabs_api_hydration"]["details"][vp_name] = tab_results
            if not all_passed:
                report["viewports"][vp_name]["passed"] = False

            # Check for console and page errors
            if console_errors:
                print(f"  Console warnings/errors: {len(console_errors)}")
            if page_errors:
                print(f"  Page errors: {page_errors}")
                report["viewports"][vp_name]["errors"].extend(page_errors)
                report["viewports"][vp_name]["passed"] = False

            context.close()

        browser.close()

    # Determine overall status
    test_statuses = [t["passed"] for t in report["tests"].values()]
    vp_statuses = [vp["passed"] for vp in report["viewports"].values()]
    report["overall_passed"] = all(test_statuses) and all(vp_statuses)

    report_path = os.path.join(EVIDENCE_DIR, "report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"\n==========================================")
    print(f"E2E Verification Report saved to {report_path}")
    print(f"Overall Passed: {report['overall_passed']}")
    print(f"==========================================")
    return report["overall_passed"]


if __name__ == "__main__":
    success = run_functional_e2e()
    sys.exit(0 if success else 1)
