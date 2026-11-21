"""Step 4 — Live Deployment & Populated-Catalog Verification against running jarvis-core.service on http://127.0.0.1:8000.
Covers:
- UX-005 (#apps-category-pills keyboard focus, Space toggle, aria-pressed="true", live 45-app category filtering)
- UX-006 (#apps-status-select counts matching live 45-app catalog & hero stats)
- BUG-002 (all 23 sidebar tabs clickable, zero overflow, no DOM nesting traps; explicit verification of YouTube, Documents, Research, Account)
- UX-001 (nav[role=tablist] vertical arrow navigation: ArrowDown advances, ArrowUp moves back)
- Live carry-overs:
  - BUG-001 (unauthenticated/guest session displays neutral role, never premature ADMIN)
  - UX-002 (guest launch denial on extension-28 renders inline in #apps-launch-status, zero dialogs, restores focus)
  - UX-004 (#sidebar-operator-card native button keyboard focus + Enter activates #tab-account)
- E-STOP safety assertion (assert visible and enabled in DOM, NEVER clicked)
- Viewports: 1440x900 and 1280x720 (1 worker, fake media)
"""

import json
import os
import subprocess
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

REPO_ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_DIR = REPO_ROOT / "docs/jarvis-ui/evidence/audit-remediation/step4-live"
LIVE_URL = "http://127.0.0.1:8000"


def get_git_revision_info():
    try:
        rev = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True).strip()
        status = subprocess.check_output(["git", "status", "--porcelain"], cwd=REPO_ROOT, text=True).strip()
        diff_stat = subprocess.check_output(["git", "diff", "--stat"], cwd=REPO_ROOT, text=True).strip()
        return {"revision": rev, "is_dirty": bool(status), "diff_stat": diff_stat}
    except Exception as e:
        return {"error": str(e)}


def main():
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

    results = {
        "suite": "Step 4 — Live Deployment & Populated-Catalog Verification",
        "live_url": LIVE_URL,
        "git": get_git_revision_info(),
        "viewports": {},
        "issues_verified": {
            "UX-005": False,
            "UX-006": False,
            "BUG-002": False,
            "UX-001": False,
            "BUG-001": False,
            "UX-002": False,
            "UX-004": False,
        },
        "safety_checks": {
            "estop_visible_and_enabled": False,
            "estop_never_clicked": True,
            "zero_native_alerts": True,
        },
        "screenshots": [],
    }

    with sync_playwright() as pw:
        with pw.chromium.launch(
            executable_path=os.getenv("CHROME_BIN") or None,
            args=[
                "--use-fake-device-for-media-stream",
                "--use-fake-ui-for-media-stream",
                "--mute-audio",
            ],
        ) as browser:
            page = browser.new_page()

            dialogs = []

            def on_dialog(dialog):
                dialogs.append({"type": dialog.type, "message": dialog.message})
                dialog.dismiss()

            page.on("dialog", on_dialog)

            # Navigate to live server
            page.goto(LIVE_URL + "/", wait_until="networkidle")

            # Verify E-STOP safety rail
            estop = page.locator("#estop-btn")
            assert estop.is_visible(), "Safety constraint violated: #estop-btn must be visible"
            assert estop.is_enabled(), "Safety constraint violated: #estop-btn must be enabled"
            results["safety_checks"]["estop_visible_and_enabled"] = True
            print("Safety check passed: #estop-btn is visible and enabled in DOM (never clicked).")

            for width, height in [(1440, 900), (1280, 720)]:
                vp_key = f"{width}x{height}"
                print(f"\n==========================================")
                print(f"--- Testing Live Viewport: {vp_key} ---")
                print(f"==========================================")
                page.set_viewport_size({"width": width, "height": height})
                page.goto(LIVE_URL + "/", wait_until="networkidle")

                # =====================================================================
                # 1. UX-001: nav[role=tablist] Vertical Arrow Navigation
                # =====================================================================
                print(f"[{vp_key}] Checking UX-001 (nav[role=tablist] keyboard navigation)...")
                page.locator("#nav-home").focus()
                assert page.evaluate("() => document.activeElement.id === 'nav-home'")

                # ArrowDown moves to next tab (#nav-apps)
                page.keyboard.press("ArrowDown")
                down_target = page.evaluate(
                    "() => ({ id: document.activeElement.id, selected: document.activeElement.getAttribute('aria-selected') })"
                )
                assert down_target["id"] == "nav-apps", f"Expected ArrowDown to focus nav-apps, got: {down_target['id']}"
                assert down_target["selected"] == "true", "Expected aria-selected='true' on nav-apps"
                assert page.locator("#tab-apps").is_visible(), "Expected #tab-apps to become visible on ArrowDown"

                # ArrowUp moves back to previous tab (#nav-home)
                page.keyboard.press("ArrowUp")
                up_target = page.evaluate(
                    "() => ({ id: document.activeElement.id, selected: document.activeElement.getAttribute('aria-selected') })"
                )
                assert up_target["id"] == "nav-home", f"Expected ArrowUp to focus nav-home, got: {up_target['id']}"
                assert up_target["selected"] == "true", "Expected aria-selected='true' on nav-home"
                assert page.locator("#tab-home").is_visible(), "Expected #tab-home to become visible on ArrowUp"

                shot_ux1 = EVIDENCE_DIR / f"ux001_keyboard_nav_{width}.png"
                page.screenshot(path=str(shot_ux1))
                results["screenshots"].append(str(shot_ux1))
                print(f"[{vp_key}] UX-001 passed (ArrowDown & ArrowUp advance focus, selection, and visible panel).")

                # =====================================================================
                # 2. BUG-002: Click Through All 23 Sidebar Tabs (Zero Overflow, No DOM Nesting Traps)
                # =====================================================================
                print(f"[{vp_key}] Checking BUG-002 (all 23 sidebar tabs navigation)...")
                tabs = page.locator("nav[role='tablist'] button[data-tab]")
                names = tabs.evaluate_all("els => els.map(e => e.dataset.tab)")
                assert len(names) == 23, f"Expected 23 unique tabs in live nav, found {len(names)}: {names}"
                assert len(names) == len(set(names)), "Duplicate tab IDs found in nav"

                for tab_name in ["youtube", "documents", "research", "account"]:
                    assert tab_name in names, f"Required tab '{tab_name}' not in nav tabs list"

                for name in names:
                    nav_btn = page.locator(f"#nav-{name}")
                    nav_btn.click(timeout=3000)
                    panel = page.locator(f"#tab-{name}")
                    assert panel.is_visible(), f"Tab panel #tab-{name} failed to become visible on click"

                    # Check parent element is #main-content (no nesting traps inside #tab-developer or elsewhere)
                    parent_id = panel.evaluate("el => el.parentElement ? el.parentElement.id : null")
                    assert parent_id == "main-content", (
                        f"DOM nesting trap detected! #tab-{name} parent is #{parent_id}, expected #main-content"
                    )

                    # Check for horizontal overflow
                    is_overflowing = panel.evaluate("el => el.scrollWidth > el.clientWidth + 4")
                    assert not is_overflowing, f"Panel #tab-{name} has unexpected horizontal overflow at {vp_key}"

                # Capture explicit screenshots for the 4 target tabs from BUG-002
                for target_tab in ["youtube", "documents", "research", "account"]:
                    page.locator(f"#nav-{target_tab}").click()
                    page.wait_for_selector(f"#tab-{target_tab}.active")
                    shot_tab = EVIDENCE_DIR / f"bug002_tab_{target_tab}_{width}.png"
                    page.screenshot(path=str(shot_tab))
                    results["screenshots"].append(str(shot_tab))

                print(f"[{vp_key}] BUG-002 passed (all 23 tabs clicked, YouTube/Docs/Research/Account verified without DOM nesting traps).")

                # =====================================================================
                # 3. UX-005: Category Pills Against Live 45-App Catalog (Keyboard Space Toggle & Filtering)
                # =====================================================================
                print(f"[{vp_key}] Checking UX-005 (apps category pills keyboard Space filtering)...")
                page.locator("#nav-apps").click()
                page.wait_for_selector("#apps-grid .app-card")

                # Ensure all 45 apps are loaded
                app_cards = page.locator("#apps-grid .app-card")
                total_initial_cards = app_cards.count()
                assert total_initial_cards == 45, f"Expected 45 initial live app cards, got {total_initial_cards}"

                # Focus "AI Agents" category pill by role and press Space
                ai_agents_btn = page.locator("#apps-category-pills button:has-text('AI Agents')")
                assert ai_agents_btn.is_visible()
                ai_agents_btn.focus()
                assert page.evaluate("() => document.activeElement.innerText.includes('AI Agents')")

                page.keyboard.press("Space")
                time.sleep(0.3)  # Allow DOM render

                # Verify aria-pressed="true"
                assert ai_agents_btn.get_attribute("aria-pressed") == "true", "Expected aria-pressed='true' on AI Agents pill"

                # Verify visible cards count matches live backend AI Agents count (6 apps)
                visible_cards = page.locator("#apps-grid .app-card")
                visible_count = visible_cards.count()
                assert visible_count == 6, f"Expected exactly 6 AI Agents apps after filter, got {visible_count}"

                shot_ux5 = EVIDENCE_DIR / f"ux005_apps_category_filtered_{width}.png"
                page.screenshot(path=str(shot_ux5))
                results["screenshots"].append(str(shot_ux5))

                # Reset back to "All Categories" via keyboard Space
                all_cats_btn = page.locator("#apps-category-pills button:has-text('All Categories')")
                all_cats_btn.focus()
                page.keyboard.press("Space")
                time.sleep(0.3)
                assert all_cats_btn.get_attribute("aria-pressed") == "true"
                assert page.locator("#apps-grid .app-card").count() == 45
                print(f"[{vp_key}] UX-005 passed (Space key activates pill, sets aria-pressed='true', filters to 6 AI agent cards, resets to 45).")

                # =====================================================================
                # 4. UX-006: Filter Dropdown Counts & Hero Stats Exact Match
                # =====================================================================
                print(f"[{vp_key}] Checking UX-006 (apps status select counts & hero stats)...")
                # Check Hero stats
                stat_tot = page.locator("#apps-stat-total").inner_text().strip()
                stat_avail = page.locator("#apps-stat-available").inner_text().strip()
                stat_plan = page.locator("#apps-stat-planned").inner_text().strip()

                assert stat_tot == "45", f"Expected #apps-stat-total to be 45, got: {stat_tot}"
                assert stat_avail == "45", f"Expected #apps-stat-available to be 45, got: {stat_avail}"
                assert stat_plan == "0", f"Expected #apps-stat-planned to be 0, got: {stat_plan}"

                # Check Dropdown option labels
                status_select = page.locator("#apps-status-select")
                options_text = status_select.evaluate(
                    "el => Array.from(el.options).map(o => ({ value: o.value, text: o.text }))"
                )
                options_map = {o["value"]: o["text"] for o in options_text}

                assert "All Statuses (45)" in options_map.get("all", ""), f"Option 'all' mismatch: {options_map.get('all')}"
                assert "Available Only (45)" in options_map.get("available", ""), f"Option 'available' mismatch: {options_map.get('available')}"
                assert "Roadmap / Planned (0)" in options_map.get("planned", ""), f"Option 'planned' mismatch: {options_map.get('planned')}"
                assert "In Development (0)" in options_map.get("in_development", ""), f"Option 'in_development' mismatch: {options_map.get('in_development')}"

                # Test selecting 'available'
                status_select.select_option("available")
                time.sleep(0.2)
                assert page.locator("#apps-grid .app-card").count() == 45

                # Test selecting 'planned' -> 0 cards, empty message shown
                status_select.select_option("planned")
                time.sleep(0.2)
                assert page.locator("#apps-grid .app-card").count() == 0
                grid_text = page.locator("#apps-grid").inner_text()
                assert "No applications found" in grid_text

                # Reset to 'all'
                status_select.select_option("all")
                time.sleep(0.2)
                assert page.locator("#apps-grid .app-card").count() == 45

                shot_ux6 = EVIDENCE_DIR / f"ux006_apps_status_counts_{width}.png"
                page.screenshot(path=str(shot_ux6))
                results["screenshots"].append(str(shot_ux6))
                print(f"[{vp_key}] UX-006 passed (Hero stats 45/45/0 and dropdown option counts exact match rendered cards).")

                # =====================================================================
                # 5. Live Carry-over: BUG-001 (No Premature ADMIN on Load/Guest)
                # =====================================================================
                print(f"[{vp_key}] Checking BUG-001 Live (neutral role badge on guest session)...")
                page.locator("#nav-account").click()
                page.wait_for_selector("#tab-account.active")

                # Live badge text for unauthenticated guest
                badge_text = page.locator("#account-role-badge").inner_text().strip().upper()
                badge_class = page.locator("#account-role-badge").get_attribute("class") or ""
                assert "ADMIN" not in badge_text, f"Security violation: Live #account-role-badge shows ADMIN prematurely: {badge_text}"
                assert "admin" not in badge_class.lower(), f"Security violation: Live badge has admin class: {badge_class}"
                assert badge_text in ("GUEST", "UNAVAILABLE", "PENDING", "OPERATOR")

                hdr_role = page.locator("#hdr-pill-role").inner_text().strip().upper()
                assert "ADMIN" not in hdr_role, f"Security violation: Live #hdr-pill-role shows ADMIN prematurely: {hdr_role}"

                shot_bug1 = EVIDENCE_DIR / f"bug001_live_guest_role_{width}.png"
                page.screenshot(path=str(shot_bug1))
                results["screenshots"].append(str(shot_bug1))
                print(f"[{vp_key}] BUG-001 Live passed (no premature ADMIN badge; unauthenticated session displays neutral/guest role).")

                # =====================================================================
                # 6. Live Carry-over: UX-002 (Guest Launch Denial Renders Inline, Zero Dialogs, Restores Focus)
                # =====================================================================
                print(f"[{vp_key}] Checking UX-002 Live (guest launch denial on extension-28)...")
                page.locator("#nav-apps").click()
                page.wait_for_selector("#apps-grid .app-card")

                # Mock out window.jarvisNotify to verify the fallback inline error path
                page.evaluate("() => { window.jarvisNotify = null; }")
                dialogs.clear()

                # Find launch button for extension-28 (AI Data Analyst, requires USER/ADMIN)
                launch_btn = page.locator("#btn-launch-extension-28")
                assert launch_btn.is_visible(), "Launch button for extension-28 not found"
                launch_btn.focus()
                launch_btn.click()

                # Wait for inline status update in #apps-launch-status
                page.wait_for_function(
                    "document.getElementById('apps-launch-status').textContent.trim().length > 0"
                )
                launch_status = page.locator("#apps-launch-status").inner_text().strip()
                assert any(kw in launch_status.lower() for kw in ["access requires", "denied", "role", "permission", "403"]), (
                    f"Expected live denial reason in #apps-launch-status, got: {launch_status}"
                )

                # Assert zero native alert/confirm dialogs
                assert len(dialogs) == 0, f"Expected zero native dialogs, got: {dialogs}"

                # Assert focus restored to the triggering Launch button
                active_id = page.evaluate("() => document.activeElement ? document.activeElement.id : null")
                assert active_id == "btn-launch-extension-28", f"Expected focus restored to btn-launch-extension-28, got: {active_id}"

                shot_ux2 = EVIDENCE_DIR / f"ux002_live_launch_denial_{width}.png"
                page.screenshot(path=str(shot_ux2))
                results["screenshots"].append(str(shot_ux2))
                print(f"[{vp_key}] UX-002 Live passed (inline denial message '{launch_status}', zero dialogs, focus restored).")

                # =====================================================================
                # 7. Live Carry-over: UX-004 (#sidebar-operator-card Keyboard Focus + Enter)
                # =====================================================================
                print(f"[{vp_key}] Checking UX-004 Live (#sidebar-operator-card keyboard activation)...")
                page.locator("#nav-home").click()
                assert not page.locator("#tab-account").is_visible(), "Expected #tab-account to be hidden initially"

                op_card = page.locator("#sidebar-operator-card")
                tag_name = op_card.evaluate("el => el.tagName.toLowerCase()")
                assert tag_name == "button", f"Expected #sidebar-operator-card to be <button>, got <{tag_name}>"

                op_card.focus()
                page.keyboard.press("Enter")

                page.wait_for_selector("#tab-account.active")
                assert page.locator("#tab-account").is_visible(), "Expected #tab-account to become visible after Enter keypress"

                shot_ux4 = EVIDENCE_DIR / f"ux004_live_sidebar_operator_{width}.png"
                page.screenshot(path=str(shot_ux4))
                results["screenshots"].append(str(shot_ux4))
                print(f"[{vp_key}] UX-004 Live passed (keyboard focus, Enter activation, #tab-account visible).")

                results["viewports"][vp_key] = "PASSED"

    for issue in ["UX-005", "UX-006", "BUG-002", "UX-001", "BUG-001", "UX-002", "UX-004"]:
        results["issues_verified"][issue] = True

    evidence_json = EVIDENCE_DIR / "step4-live-verification.json"
    with open(evidence_json, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"\n=======================================================")
    print(f"All Step 4 live checks PASSED cleanly across both viewports!")
    print(f"Evidence saved to: {evidence_json}")
    print(f"Total screenshots captured: {len(results['screenshots'])}")
    print(f"=======================================================")


if __name__ == "__main__":
    main()
