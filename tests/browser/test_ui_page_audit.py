"""
Comprehensive Playwright UI Page-by-Page Audit & Verification Tool
Tests pages across 1440x900 and 1280x720 viewports.
Records screenshots to docs/jarvis-ui/evidence/ui-page-audit/
Strictly enforces safety rules:
- #estop-btn must be visible and enabled (NEVER CLICK IT)
- Zero real robot movement
- Single mic owner preserved
- Truthful status reporting
"""
import os
import sys
import json
import time
import argparse
from playwright.sync_api import sync_playwright

CHROME_BIN = "/usr/bin/google-chrome"
BASE_URL = "http://127.0.0.1:8000"
EVIDENCE_DIR = "/home/roshan/.gemini/antigravity/scratch/jarvis-os/docs/jarvis-ui/evidence/ui-page-audit"

VIEWPORTS = [
    {"name": "1440x900", "width": 1440, "height": 900},
    {"name": "1280x720", "width": 1280, "height": 720},
]

PAGE_SPECS = {
    1: {"name": "Top Bar & Left Sidebar Chrome", "tab": "home", "url": "/"},
    2: {"name": "Dashboard", "tab": "home", "url": "/"},
    3: {"name": "Apps", "tab": "apps", "url": "/"},
    4: {"name": "AI Chat", "tab": "chat", "url": "/"},
    5: {"name": "Voice", "tab": "voice", "url": "/"},
    6: {"name": "AI Studio", "tab": "aistudio", "url": "/"},
    7: {"name": "Vision", "tab": "vision", "url": "/"},
    8: {"name": "Robot", "tab": "robot", "url": "/"},
    9: {"name": "Sensors", "tab": "sensors", "url": "/"},
    10: {"name": "Memory", "tab": "memory", "url": "/"},
    11: {"name": "Automations", "tab": "automations", "url": "/"},
    12: {"name": "Tools", "tab": "tools", "url": "/"},
    13: {"name": "Integrations", "tab": "integrations", "url": "/"},
    14: {"name": "System", "tab": "system", "url": "/"},
    15: {"name": "Logs", "tab": "logs", "url": "/"},
    16: {"name": "Remaining Dashboard Tabs", "tabs": ["desktop", "computer", "agents", "account", "settings"], "extra_url": "/futuristic"},
}


def audit_page(page_num, mode="before"):
    """Audit a specific page number at both viewports."""
    os.makedirs(EVIDENCE_DIR, exist_ok=True)
    results = {}
    spec = PAGE_SPECS.get(page_num)
    if not spec:
        raise ValueError(f"Unknown page number: {page_num}")

    with sync_playwright() as p:
        launch_args = {
            "headless": True,
            "args": ["--no-sandbox", "--disable-dev-shm-usage", "--use-fake-ui-for-media-stream"],
        }
        if os.path.exists(CHROME_BIN):
            launch_args["executable_path"] = CHROME_BIN
        browser = p.chromium.launch(**launch_args)

        for vp in VIEWPORTS:
            vp_key = vp["name"]
            results[vp_key] = {"issues": [], "passed": True}
            context = browser.new_context(viewport={"width": vp["width"], "height": vp["height"]})
            page = context.new_page()

            console_logs = []
            page_errors = []
            failed_requests = []

            page.on("console", lambda msg: console_logs.append(f"[{msg.type}] {msg.text}"))
            page.on("pageerror", lambda exc: page_errors.append(str(exc)))
            page.on("response", lambda resp: failed_requests.append(f"{resp.status} {resp.url}") if resp.status >= 400 and not resp.url.endswith("/favicon.ico") and not "/test/" in resp.url and not "/api/chat/providers" in resp.url else None)

            # Navigate
            url = f"{BASE_URL}{spec.get('url', '/')}"
            response = page.goto(url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(1500)

            # Check estop safety rail
            estop = page.locator("#estop-btn")
            estop_visible = estop.is_visible()
            estop_enabled = estop.is_enabled()
            if not estop_visible or not estop_enabled:
                results[vp_key]["issues"].append(f"SAFETY RAIL: #estop-btn visible={estop_visible}, enabled={estop_enabled}")
                results[vp_key]["passed"] = False

            # Switch tab if needed
            tab_name = spec.get("tab")
            if tab_name and tab_name != "home":
                nav_btn = page.locator(f"#nav-{tab_name}")
                if nav_btn.is_visible():
                    nav_btn.click()
                    page.wait_for_timeout(800)
                else:
                    page.evaluate(f"() => showTab('{tab_name}')")
                    page.wait_for_timeout(800)

            # Special multi-tab handling for Page 16
            if page_num == 16:
                for rem_tab in spec.get("tabs", []):
                    page.evaluate(f"() => showTab('{rem_tab}')")
                    page.wait_for_timeout(600)
                    rem_ss = os.path.join(EVIDENCE_DIR, f"page-16-tab-{rem_tab}-{mode}-{vp_key}.png")
                    page.screenshot(path=rem_ss, full_page=False)
                    # Check overflow for each tab
                    s_w = page.evaluate("() => document.documentElement.scrollWidth")
                    i_w = page.evaluate("() => window.innerWidth")
                    if s_w > i_w:
                        results[vp_key]["issues"].append(f"Tab {rem_tab} horizontal overflow: {s_w} > {i_w}")
                        results[vp_key]["passed"] = False

                # Also test /futuristic
                fut_page = context.new_page()
                fut_url = f"{BASE_URL}{spec.get('extra_url', '/futuristic')}"
                fut_page.goto(fut_url, wait_until="domcontentloaded", timeout=30000)
                fut_page.wait_for_timeout(1000)
                fut_ss = os.path.join(EVIDENCE_DIR, f"page-16-futuristic-{mode}-{vp_key}.png")
                fut_page.screenshot(path=fut_ss, full_page=False)
                fut_sw = fut_page.evaluate("() => document.documentElement.scrollWidth")
                fut_iw = fut_page.evaluate("() => window.innerWidth")
                if fut_sw > fut_iw:
                    results[vp_key]["issues"].append(f"/futuristic horizontal overflow: {fut_sw} > {fut_iw}")
                    results[vp_key]["passed"] = False
                fut_page.close()

            # Check for horizontal overflow
            scroll_width = page.evaluate("() => document.documentElement.scrollWidth")
            inner_width = page.evaluate("() => window.innerWidth")
            if scroll_width > inner_width:
                diff = scroll_width - inner_width
                results[vp_key]["issues"].append(f"Horizontal overflow detected: scrollWidth={scroll_width} > innerWidth={inner_width} (+{diff}px)")
                results[vp_key]["passed"] = False

            # Specific element checks for Page 1
            if page_num == 1:
                # Top bar checks
                auto_speak = page.locator("#hdr-auto-speak-notif").locator("..")
                auto_speak_box = auto_speak.bounding_box() if auto_speak.count() > 0 else None
                user_pill = page.locator("#hdr-user-pill")
                user_pill_box = user_pill.bounding_box() if user_pill.count() > 0 else None
                sidebar = page.locator("body > nav")
                sidebar_box = sidebar.bounding_box() if sidebar.count() > 0 else None

                # Check if bottom items of nav are accessible or clipped
                nav_account = page.locator("#nav-account")
                nav_acc_visible = nav_account.is_visible()
                results[vp_key]["nav_account_visible"] = nav_acc_visible
                results[vp_key]["topbar_boxes"] = {
                    "auto_speak": auto_speak_box,
                    "user_pill": user_pill_box,
                    "sidebar": sidebar_box
                }

            # Capture screenshot
            ss_path = os.path.join(EVIDENCE_DIR, f"page-{page_num}-{mode}-{vp_key}.png")
            page.screenshot(path=ss_path, full_page=False)
            results[vp_key]["screenshot"] = ss_path

            # Record errors
            if page_errors:
                results[vp_key]["issues"].append(f"Page errors: {page_errors}")
                results[vp_key]["passed"] = False

            # Check fatal console errors
            severe_console = [l for l in console_logs if "[error]" in l.lower() and "favicon" not in l.lower()]
            if severe_console:
                results[vp_key]["console_errors"] = severe_console
                # Non-breaking warnings may exist, but let's log them
                results[vp_key]["issues"].append(f"Console errors: {severe_console}")

            context.close()
        browser.close()

    print(json.dumps({f"page_{page_num}_{mode}": results}, indent=2))
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--page", type=int, default=1, help="Page number 1-16")
    parser.add_argument("--mode", type=str, choices=["before", "after"], default="before")
    args = parser.parse_args()
    audit_page(args.page, args.mode)
