"""Offline UI regression check and Step 3 audit remediation verification.
MOCK backend; all browser traffic is intercepted on http://audit.invalid/.
Covers:
- BUG-001 (#account-role-badge delayed, guest, and admin hydration)
- UX-002 (#tab-apps launch denial inline feedback, zero native dialogs, focus restoration)
- UX-003 (#tab-settings inline feedback in #settings-save-status, zero native alert() dialogs)
- UX-004 (#sidebar-operator-card keyboard activation via Enter to #tab-account)
- E-STOP safety assertion (assert visible/enabled, NEVER clicked)
- 23 tab panels sweep and keyboard navigation at 1440x900 and 1280x720
"""

import json
import os
import subprocess
import time
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright

REPO_ROOT = Path(__file__).resolve().parents[2]
STATIC = REPO_ROOT / "apps/dashboard/static"
EVIDENCE_DIR = REPO_ROOT / "docs/jarvis-ui/evidence/audit-remediation"


class MockBackendState:
    def __init__(self):
        self.identity_delayed = False
        self.identity_delay_s = 0.4
        self.role = "PENDING"
        self.display_name = "Operator"
        self.admin_enrolled = True
        self.saved_settings = {}
        self.dialogs = []
        self.applications = [
            {
                "id": "extension-28",
                "name": "AI Data Analyst",
                "category": "ai_agents",
                "description": "Autonomous data analysis and visual insights",
                "status": "available",
                "permissions": ["admin"],
                "resource_profile": "medium",
            }
        ]


def create_serve_handler(state: MockBackendState):
    def serve(route):
        url = urlsplit(route.request.url)
        if url.hostname != "audit.invalid":
            return route.abort()
        path = url.path
        method = route.request.method

        if path == "/api/identity/status":
            if state.identity_delayed:
                time.sleep(state.identity_delay_s)
            role = None if state.role == "PENDING" else state.role
            active_user = (
                None
                if state.role == "PENDING"
                else {
                    "display_name": state.display_name,
                    "role": state.role,
                }
            )
            return route.fulfill(
                json={
                    "is_admin_enrolled": state.admin_enrolled,
                    "active_user": active_user,
                    "authorization_role": role,
                }
            )
        elif path == "/api/account/profile":
            if state.identity_delayed:
                time.sleep(state.identity_delay_s)
            role = None if state.role == "PENDING" else state.role
            user = (
                None
                if state.role == "PENDING"
                else {
                    "display_name": state.display_name,
                    "role": state.role,
                    "bio": "Lead Operator" if state.role == "ADMIN" else "Guest Operator",
                    "callsign": "Falcon" if state.role == "ADMIN" else "Guest",
                }
            )
            return route.fulfill(
                json={
                    "user": user,
                    "session_remaining_s": 300 if state.role == "ADMIN" else 0,
                    "session_ttl_s": 300,
                }
            )
        elif path == "/api/apps/catalog":
            return route.fulfill(
                json={
                    "total": len(state.applications),
                    "applications": state.applications,
                }
            )
        elif path.startswith("/api/apps/launch/"):
            return route.fulfill(
                status=403,
                json={"detail": "Adapter launch denied"},
            )
        elif path == "/api/settings":
            return route.fulfill(
                json={
                    "categories": {
                        "core": {
                            "name": "Core System",
                            "debug_mode": False,
                            "log_level": "INFO",
                        }
                    }
                }
            )
        elif path.startswith("/api/settings/"):
            if method == "POST":
                data = route.request.post_data_json or {}
                state.saved_settings[path] = data
                return route.fulfill(json={"status": "ok", "saved": data})
            return route.fulfill(json={"status": "ok"})
        elif path.startswith("/api/"):
            return route.fulfill(json={})

        filename = (STATIC / (path.removeprefix("/static/").lstrip("/") or "index.html")).resolve()
        if filename.is_relative_to(STATIC) and filename.is_file():
            return route.fulfill(path=filename)
        route.abort()

    return serve


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
    state = MockBackendState()
    serve = create_serve_handler(state)

    results = {
        "suite": "Step 3 — Offline/Intercepted UI Verification",
        "git": get_git_revision_info(),
        "viewports": {},
        "issues_verified": {
            "BUG-001": False,
            "UX-002": False,
            "UX-003": False,
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
            page = browser.new_page(service_workers="block")
            page.route("**/*", serve)
            page.route_web_socket("**/*", lambda ws: None)

            def on_dialog(dialog):
                state.dialogs.append({"type": dialog.type, "message": dialog.message})
                if dialog.type == "confirm":
                    dialog.accept()
                elif dialog.type == "prompt":
                    dialog.accept("1234")
                else:
                    dialog.dismiss()

            page.on("dialog", on_dialog)

            page.goto("http://audit.invalid/", wait_until="domcontentloaded")

            # Verify E-STOP safety rail
            estop = page.locator("#estop-btn")
            assert estop.is_visible(), "Safety constraint violated: #estop-btn must be visible"
            assert estop.is_enabled(), "Safety constraint violated: #estop-btn must be enabled"
            results["safety_checks"]["estop_visible_and_enabled"] = True
            print("Safety verification passed: #estop-btn is visible and enabled (never clicked).")

            for width, height in [(1440, 900), (1280, 720)]:
                vp_key = f"{width}x{height}"
                print(f"\n--- Testing Viewport: {vp_key} ---")
                page.set_viewport_size({"width": width, "height": height})
                state.identity_delayed = False
                state.role = "PENDING"
                state.display_name = "Operator"
                page.goto("http://audit.invalid/", wait_until="domcontentloaded")

                # 1. Baseline Panel Sweeps
                tabs = page.locator("nav [data-tab]")
                names = tabs.evaluate_all("els => els.map(e => e.dataset.tab)")
                assert len(names) == len(set(names)) and len(names) >= 23
                for name in names:
                    page.locator("#nav-" + name).click(timeout=2000)
                    assert page.locator("#tab-" + name).is_visible(), name

                # Tab keyboard navigation check (ArrowDown from Home)
                page.locator("#nav-home").focus()
                page.keyboard.press("ArrowDown")
                assert page.locator("#nav-apps").evaluate(
                    "e => e === document.activeElement && e.getAttribute('aria-selected') === 'true'"
                )

                # Category pills keyboard check (Space)
                page.locator("#apps-category-pills button").nth(1).focus()
                page.keyboard.press("Space")
                assert (
                    page.locator("#apps-category-pills button").nth(1).get_attribute("aria-pressed") == "true"
                )
                print(f"{vp_key}: 23 panels and keyboard navigation checks passed")

                # =====================================================================
                # CHECK 1: BUG-001 (#account-role-badge delayed, guest, and admin)
                # =====================================================================
                print(f"[{vp_key}] Checking BUG-001 (#account-role-badge)...")
                state.identity_delayed = True
                state.role = "PENDING"
                state.display_name = "Operator"

                page.evaluate("showTab('account')")
                # Immediate check while identity response is delayed:
                role_badge_initial = page.locator("#account-role-badge").inner_text().strip()
                assert role_badge_initial.upper() in ("PENDING", "UNAVAILABLE"), (
                    f"Expected #account-role-badge to show Pending or Unavailable before confirmation, got '{role_badge_initial}'"
                )
                assert "admin" not in page.locator("#account-role-badge").get_attribute("class").lower()
                assert "ADMIN" not in role_badge_initial.upper()
                hdr_pill_initial = page.locator("#hdr-pill-role").inner_text().strip()
                assert hdr_pill_initial.upper() in ("PENDING", "UNAVAILABLE", "GUEST")
                assert "ADMIN" not in hdr_pill_initial.upper()

                shot_delayed = EVIDENCE_DIR / f"bug001_role_badge_delayed_{width}.png"
                page.screenshot(path=str(shot_delayed))
                results["screenshots"].append(str(shot_delayed))

                # Hydrate as Guest
                state.identity_delayed = False
                state.role = "GUEST"
                state.display_name = "Guest"
                page.evaluate(
                    """() => {
                    if (window.AccountCenter) {
                        window.AccountCenter.refreshIdentityStatus();
                        window.AccountCenter.loadAccountCenter();
                    }
                }"""
                )
                page.wait_for_function(
                    "document.getElementById('account-role-badge').textContent.trim() === 'GUEST'"
                )
                assert page.locator("#account-role-badge").inner_text() == "GUEST"
                assert "guest" in page.locator("#account-role-badge").get_attribute("class")

                shot_guest = EVIDENCE_DIR / f"bug001_role_badge_guest_{width}.png"
                page.screenshot(path=str(shot_guest))
                results["screenshots"].append(str(shot_guest))

                # Hydrate as Authorized Operator (ADMIN)
                state.role = "ADMIN"
                state.display_name = "Roshan"
                page.evaluate(
                    """() => {
                    if (window.AccountCenter) {
                        window.AccountCenter.refreshIdentityStatus();
                        window.AccountCenter.loadAccountCenter();
                    }
                }"""
                )
                page.wait_for_function(
                    "document.getElementById('account-role-badge').textContent.trim() === 'ADMIN'"
                )
                assert page.locator("#account-role-badge").inner_text() == "ADMIN"
                assert "admin" in page.locator("#account-role-badge").get_attribute("class")

                shot_admin = EVIDENCE_DIR / f"bug001_role_badge_admin_{width}.png"
                page.screenshot(path=str(shot_admin))
                results["screenshots"].append(str(shot_admin))
                print(f"[{vp_key}] BUG-001 passed (delayed 'Pending', guest hydration, authorized admin hydration).")

                # =====================================================================
                # CHECK 2: UX-002 (#tab-apps launch denial & focus restoration)
                # =====================================================================
                print(f"[{vp_key}] Checking UX-002 (#tab-apps launch denial)...")
                state.dialogs.clear()
                page.evaluate(
                    """() => {
                    showTab('apps');
                    window.jarvisNotify = null;
                    const allBtn = document.querySelector('#apps-category-pills button');
                    if (allBtn && typeof selectAppCategory === 'function') {
                        selectAppCategory('all', allBtn);
                    }
                }"""
                )
                page.wait_for_selector("#btn-launch-extension-28")
                launch_btn = page.locator("#btn-launch-extension-28")
                launch_btn.focus()
                launch_btn.click()

                page.wait_for_function(
                    "document.getElementById('apps-launch-status').textContent.includes('Adapter launch denied')"
                )
                status_text = page.locator("#apps-launch-status").inner_text()
                assert "Adapter launch denied" in status_text, f"Expected denial message, got: {status_text}"

                # Assert zero native alert/confirm dialogs
                assert len(state.dialogs) == 0, f"Expected zero native dialogs, got: {state.dialogs}"

                # Assert focus restored to triggering launch button
                active_element_id = page.evaluate("() => document.activeElement ? document.activeElement.id : null")
                assert active_element_id == "btn-launch-extension-28", (
                    f"Expected focus on 'btn-launch-extension-28', got: {active_element_id}"
                )

                shot_ux2 = EVIDENCE_DIR / f"ux002_apps_launch_denial_{width}.png"
                page.screenshot(path=str(shot_ux2))
                results["screenshots"].append(str(shot_ux2))
                print(f"[{vp_key}] UX-002 passed (zero dialogs, accessible inline error, focus restored).")

                # =====================================================================
                # CHECK 3: UX-003 (#tab-settings inline feedback & zero alert dialogs)
                # =====================================================================
                print(f"[{vp_key}] Checking UX-003 (#tab-settings inline feedback)...")
                state.dialogs.clear()
                page.evaluate("showTab('settings')")
                page.wait_for_selector("#set-debug_mode")

                # Reversible toggle
                page.locator("#set-debug_mode").click()

                # Trigger save
                save_btn = page.locator("#tab-settings button:has-text('Save Changes')")
                save_btn.click()

                page.wait_for_function(
                    "document.getElementById('settings-save-status').textContent.includes('Saved CORE settings.')"
                )
                save_status = page.locator("#settings-save-status").inner_text()
                assert "Saved CORE settings." in save_status, f"Expected save confirmation, got: {save_status}"

                # Assert zero alert dialogs
                alert_dialogs = [d for d in state.dialogs if d["type"] == "alert"]
                assert len(alert_dialogs) == 0, f"Expected zero alert dialogs, got: {alert_dialogs}"

                shot_ux3 = EVIDENCE_DIR / f"ux003_settings_inline_status_{width}.png"
                page.screenshot(path=str(shot_ux3))
                results["screenshots"].append(str(shot_ux3))
                print(f"[{vp_key}] UX-003 passed (inline save feedback, zero native alerts).")

                # =====================================================================
                # CHECK 4: UX-004 (#sidebar-operator-card keyboard activation)
                # =====================================================================
                print(f"[{vp_key}] Checking UX-004 (#sidebar-operator-card keyboard activation)...")
                page.evaluate("showTab('home')")
                assert not page.locator("#tab-account").is_visible(), "Expected #tab-account to be hidden initially"

                # Locate by button role / native button tag
                op_card = page.locator("#sidebar-operator-card")
                tag_name = op_card.evaluate("e => e.tagName.toLowerCase()")
                assert tag_name == "button", f"Expected #sidebar-operator-card to be <button>, got <{tag_name}>"

                # Focus via keyboard, press Enter
                op_card.focus()
                page.keyboard.press("Enter")

                page.wait_for_selector("#tab-account.active")
                assert page.locator("#tab-account").is_visible(), "Expected #tab-account to become visible after Enter"

                shot_ux4 = EVIDENCE_DIR / f"ux004_sidebar_operator_enter_{width}.png"
                page.screenshot(path=str(shot_ux4))
                results["screenshots"].append(str(shot_ux4))
                print(f"[{vp_key}] UX-004 passed (keyboard focus, Enter activation, #tab-account visible).")

                results["viewports"][vp_key] = "PASSED"

    results["issues_verified"]["BUG-001"] = True
    results["issues_verified"]["UX-002"] = True
    results["issues_verified"]["UX-003"] = True
    results["issues_verified"]["UX-004"] = True

    evidence_json = EVIDENCE_DIR / "step3-offline-ui-verification.json"
    with open(evidence_json, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\nAll Step 3 checks passed at both viewports! Evidence saved to {evidence_json}")


if __name__ == "__main__":
    main()
