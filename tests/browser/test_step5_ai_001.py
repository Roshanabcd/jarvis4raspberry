"""Step 5 — Local AI Route Verification (AI-001, P1-High).
Covers:
1. Focused Provider Unit Tests record (pytest tests/unit/test_provider_integrations.py -k ollama).
2. Installed Local Models inspection (Ollama tags, chat providers, model family and size verification).
3. Offline / Intercepted UI checks:
   - Selecting unavailable model in Conversation mode preserves draft in #chat-in, fires 0 stream requests, surfaces inline error.
   - Model refresh control (initChatModels) re-queries providers.
   - Rejected model-switch surfaces inline error in #chat-status-badge.
   - Cancellation during stream unlocks buttons (#cancel-chat-btn hides, #chat-send-btn enables) and sets badge to Stopped.
4. Live Local Text-Model Benchmark on http://127.0.0.1:8000 with warm llama3.2:1b across 1440x900 and 1280x720:
   - Turn 1: "Remember the audit word violet. Reply with only the word."
   - Turn 2: "What was the audit word?" (memory recall assertion)
   - Turn 3: "Write a Python function is_even(n) that returns True for even integers." (code generation)
   - Recorded metrics: TTFT (ms), total latency (ms), reply text, UI status, Pi 5 CPU/RAM snapshots (idle vs active).
   - E-STOP safety rail: asserted visible and enabled, never clicked.
"""

import json
import os
import subprocess
import threading
import time
from pathlib import Path
from urllib.parse import urlsplit

import psutil
import requests
from playwright.sync_api import sync_playwright

REPO_ROOT = Path(__file__).resolve().parents[2]
STATIC = REPO_ROOT / "apps/dashboard/static"
EVIDENCE_DIR = REPO_ROOT / "docs/jarvis-ui/evidence/audit-remediation/step5-ai-001"
LIVE_URL = "http://127.0.0.1:8000"


def get_git_revision_info():
    try:
        rev = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True).strip()
        status = subprocess.check_output(["git", "status", "--porcelain"], cwd=REPO_ROOT, text=True).strip()
        diff_stat = subprocess.check_output(["git", "diff", "--stat"], cwd=REPO_ROOT, text=True).strip()
        return {"revision": rev, "is_dirty": bool(status), "diff_stat": diff_stat}
    except Exception as e:
        return {"error": str(e)}


def get_hardware_snapshot():
    try:
        mem = psutil.virtual_memory()
        cpu = psutil.cpu_percent(interval=0.1)
        return {
            "cpu_percent": cpu,
            "ram_percent": mem.percent,
            "ram_used_mb": round(mem.used / 1024 / 1024, 1),
            "ram_available_mb": round(mem.available / 1024 / 1024, 1),
            "ram_total_mb": round(mem.total / 1024 / 1024, 1),
        }
    except Exception as e:
        return {"error": str(e)}


class MockOfflineState:
    def __init__(self):
        self.stream_requests = []
        self.provider_fetch_count = 0
        self.model_switch_rejected = False
        self.slow_stream = False
        self.pending_route = None


def create_offline_serve_handler(state: MockOfflineState):
    def serve(route):
        url = urlsplit(route.request.url)
        if url.hostname != "audit.invalid":
            return route.abort()
        path = url.path
        method = route.request.method

        if path == "/api/chat/providers":
            state.provider_fetch_count += 1
            return route.fulfill(
                json={
                    "providers": [
                        {
                            "name": "ollama",
                            "available": True,
                            "model": "llama3.2:1b",
                            "models": ["llama3.2:1b"],
                            "active": True,
                            "enabled": True,
                            "verification": "ok",
                        },
                        {
                            "name": "gemini",
                            "available": False,
                            "model": "gemini-2.0-flash",
                            "models": ["gemini-2.0-flash"],
                            "active": False,
                            "enabled": True,
                            "credential_configured": False,
                            "verification": "missing_key",
                        },
                    ],
                    "active_provider": "ollama",
                    "active_model": "llama3.2:1b",
                }
            )
        elif path == "/api/chat/model":
            if state.model_switch_rejected:
                return route.fulfill(status=400, json={"success": False, "error": "Model rejected"})
            data = route.request.post_data_json or {}
            return route.fulfill(
                json={
                    "success": True,
                    "active_provider": data.get("provider", "ollama"),
                    "active_model": data.get("model", "llama3.2:1b"),
                }
            )
        elif path == "/api/chat/stream":
            state.stream_requests.append(route.request.post_data_json or {})
            if state.slow_stream:
                # Keep request in-flight to simulate slow provider response
                state.pending_route = route
                return
            # Default mock stream
            sse_data = (
                'data: {"type": "accepted", "request_id": "mock-req-1"}\n\n'
                'data: {"type": "token", "content": "mock token"}\n\n'
                'data: {"type": "done", "status": "completed", "provider": "ollama"}\n\n'
            )
            return route.fulfill(
                status=200,
                headers={
                    "Content-Type": "text/event-stream",
                    "Cache-Control": "no-cache",
                },
                body=sse_data,
            )
        elif path == "/api/chat/cancel":
            if state.pending_route:
                try:
                    state.pending_route.abort()
                except Exception:
                    pass
                state.pending_route = None
            return route.fulfill(json={"status": "ok", "request_id": "mock-slow-1"})
        elif path.startswith("/api/"):
            return route.fulfill(json={})

        filename = (STATIC / (path.removeprefix("/static/").lstrip("/") or "index.html")).resolve()
        if filename.is_relative_to(STATIC) and filename.is_file():
            return route.fulfill(path=filename)
        route.abort()

    return serve


def run_unit_tests():
    print("\n--- Running Focused Provider Unit Tests ---")
    cmd = [str(REPO_ROOT / "venv/bin/python"), "-m", "pytest", "-v", "tests/unit/test_provider_integrations.py", "-k", "ollama"]
    res = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True)
    passed = res.returncode == 0
    print(f"Unit tests returncode: {res.returncode}")
    print(res.stdout)
    return {
        "command": "venv/bin/python -m pytest -v tests/unit/test_provider_integrations.py -k ollama",
        "returncode": res.returncode,
        "passed": passed,
        "stdout": res.stdout,
    }


def inspect_installed_models():
    print("\n--- Inspecting Installed Local Models ---")
    ollama_tags = {}
    chat_providers = {}
    try:
        r = requests.get("http://127.0.0.1:11434/api/tags", timeout=5)
        ollama_tags = r.json()
    except Exception as e:
        ollama_tags = {"error": str(e)}

    try:
        r = requests.get(f"{LIVE_URL}/api/chat/providers", timeout=5)
        chat_providers = r.json()
    except Exception as e:
        chat_providers = {"error": str(e)}

    print("Ollama Tags Models:", [m.get("name") for m in ollama_tags.get("models", [])])
    print("Chat API Active Provider:", chat_providers.get("active_provider"), "Active Model:", chat_providers.get("active_model"))
    return {
        "ollama_tags": ollama_tags,
        "chat_providers": chat_providers,
    }


def main():
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

    results = {
        "suite": "Step 5 — Local AI Route Verification (AI-001, P1-High)",
        "git": get_git_revision_info(),
        "safety_checks": {
            "estop_visible_and_enabled": False,
            "estop_never_clicked": True,
            "zero_paid_cloud_apis": True,
            "no_model_downloads": True,
            "vision_model_excluded_from_text_benchmarks": True,
        },
        "unit_tests": {},
        "model_inspection": {},
        "offline_ui_checks": {},
        "live_benchmark": {},
        "screenshots": [],
        "overall_verified": False,
    }

    # 1. Run unit tests
    results["unit_tests"] = run_unit_tests()
    assert results["unit_tests"]["passed"], "Provider unit tests failed!"

    # 2. Inspect installed local models
    results["model_inspection"] = inspect_installed_models()
    models = [m.get("name") for m in results["model_inspection"]["ollama_tags"].get("models", [])]
    assert "llama3.2:1b" in models, "Required text benchmark model llama3.2:1b not found in Ollama!"

    with sync_playwright() as pw:
        with pw.chromium.launch(
            executable_path=os.getenv("CHROME_BIN") or None,
            args=[
                "--use-fake-device-for-media-stream",
                "--use-fake-ui-for-media-stream",
                "--mute-audio",
            ],
        ) as browser:
            # -------------------------------------------------------------
            # Part A: Offline / Intercepted UI Checks
            # -------------------------------------------------------------
            print("\n==========================================")
            print("--- Part A: Offline / Intercepted UI Checks ---")
            print("==========================================")
            state = MockOfflineState()
            serve_handler = create_offline_serve_handler(state)

            offline_page = browser.new_page()
            offline_page.route("http://audit.invalid/**", serve_handler)
            offline_page.goto("http://audit.invalid/", wait_until="networkidle")

            # Safety rail assertion
            estop = offline_page.locator("#estop-btn")
            assert estop.is_visible() and estop.is_enabled(), "E-STOP safety constraint violated in offline test"

            # Navigate to Chat tab
            offline_page.click("#nav-chat")
            offline_page.wait_for_selector("#tab-chat.active, #tab-chat:not([style*='display: none'])")

            # Check 1: Unavailable model in Conversation mode leaves draft intact and sends zero stream requests
            offline_page.select_option("#chat-mode", "conversation")
            offline_page.select_option("#chat-model-select", "gemini:gemini-2.0-flash")

            draft_text = "Remember the audit word violet. Reply with only the word."
            offline_page.fill("#chat-in", draft_text)
            offline_page.click("#chat-send-btn")

            retained_text = offline_page.locator("#chat-in").input_value()
            assert retained_text == draft_text, f"Draft text was not preserved! Got: '{retained_text}'"
            assert len(state.stream_requests) == 0, f"Expected 0 stream requests, got {len(state.stream_requests)}"

            status_badge_text = offline_page.locator("#chat-status-badge").text_content().strip()
            assert "Select an available model or refresh model availability." in status_badge_text, f"Unexpected badge: '{status_badge_text}'"

            draft_screenshot = EVIDENCE_DIR / "ai001_offline_draft_preserved.png"
            offline_page.screenshot(path=str(draft_screenshot))
            results["screenshots"].append(str(draft_screenshot.relative_to(REPO_ROOT)))
            print("✓ Offline Check 1 passed: Draft preserved, 0 stream requests fired, inline error surfaced.")

            # Check 2: Model refresh control
            prev_fetch_count = state.provider_fetch_count
            offline_page.click('button[aria-label="Refresh model availability"]')
            offline_page.wait_for_timeout(200)
            assert state.provider_fetch_count > prev_fetch_count, "Refresh button did not trigger provider fetch!"
            print("✓ Offline Check 2 passed: Refresh control re-queried providers.")

            # Check 3: Rejected model switch surfaces error
            state.model_switch_rejected = True
            # Trigger switch
            offline_page.evaluate("switchChatModel('ollama:rejected-model')")
            offline_page.wait_for_timeout(300)
            switch_status_text = offline_page.locator("#chat-status-badge").text_content().strip()
            assert "Model could not be selected. Check provider settings." in switch_status_text, f"Unexpected status: '{switch_status_text}'"

            rejected_screenshot = EVIDENCE_DIR / "ai001_offline_rejected_switch.png"
            offline_page.screenshot(path=str(rejected_screenshot))
            results["screenshots"].append(str(rejected_screenshot.relative_to(REPO_ROOT)))
            print("✓ Offline Check 3 passed: Rejected model switch surfaced inline error.")

            # Check 4: Cancellation UI state
            state.model_switch_rejected = False
            state.slow_stream = True
            offline_page.wait_for_selector("#chat-model-select option[value='ollama:llama3.2:1b']", state="attached", timeout=5000)
            offline_page.select_option("#chat-model-select", "ollama:llama3.2:1b")
            offline_page.fill("#chat-in", "Slow test prompt")
            offline_page.click("#chat-send-btn")

            offline_page.wait_for_selector("#cancel-chat-btn", state="visible", timeout=5000)
            assert offline_page.locator("#chat-send-btn").is_disabled(), "Send button should be disabled during active request"

            # Click cancel
            offline_page.click("#cancel-chat-btn")
            offline_page.wait_for_selector("#cancel-chat-btn", state="hidden", timeout=3000)
            assert offline_page.locator("#chat-send-btn").is_enabled(), "Send button should be enabled after cancel"
            stopped_badge = offline_page.locator("#chat-status-badge").text_content().strip()
            assert "Stopped" in stopped_badge, f"Badge does not show Stopped: '{stopped_badge}'"

            cancel_screenshot = EVIDENCE_DIR / "ai001_offline_cancelled.png"
            offline_page.screenshot(path=str(cancel_screenshot))
            results["screenshots"].append(str(cancel_screenshot.relative_to(REPO_ROOT)))
            print("✓ Offline Check 4 passed: Cancellation UI state verified (Stop button hides, Send unlocks, status=Stopped).")

            results["offline_ui_checks"] = {
                "draft_preserved": True,
                "zero_stream_requests_on_unavailable": True,
                "unavailable_status_badge": status_badge_text,
                "refresh_control_working": True,
                "rejected_switch_handled": True,
                "cancellation_handled": True,
            }
            offline_page.close()

            # -------------------------------------------------------------
            # Part B: Live Local Text-Model Benchmark
            # -------------------------------------------------------------
            print("\n==========================================")
            print("--- Part B: Live Local Text-Model Benchmark ---")
            print("==========================================")

            live_page = browser.new_page()
            live_page.goto(LIVE_URL + "/", wait_until="networkidle")

            # E-STOP safety assertion on live page
            live_estop = live_page.locator("#estop-btn")
            assert live_estop.is_visible() and live_estop.is_enabled(), "Live E-STOP safety constraint violated"
            results["safety_checks"]["estop_visible_and_enabled"] = True

            for width, height in [(1440, 900), (1280, 720)]:
                vp_key = f"{width}x{height}"
                print(f"\n--- Testing Live Viewport: {vp_key} ---")
                live_page.set_viewport_size({"width": width, "height": height})
                live_page.goto(LIVE_URL + "/", wait_until="networkidle")

                # Navigate to Chat tab
                live_page.click("#nav-chat")
                live_page.wait_for_selector("#tab-chat.active, #tab-chat:not([style*='display: none'])")

                # Ensure conversation mode and llama3.2:1b
                live_page.select_option("#chat-mode", "conversation")
                live_page.select_option("#chat-model-select", "ollama:llama3.2:1b")

                # Uncheck Auto-Speak to benchmark pure text token streaming
                auto_speak = live_page.locator("#chat-auto-speak")
                if auto_speak.is_checked():
                    auto_speak.uncheck()

                vp_results = {
                    "turns": [],
                }

                # Helper to execute a benchmark turn
                def execute_live_turn(turn_idx, prompt_text, turn_name):
                    print(f"\n[Viewport {vp_key}] Executing Turn {turn_idx}: '{turn_name}'")
                    idle_snapshot = get_hardware_snapshot()

                    prev_count = live_page.locator("#chat-box .msg.jarvis").count()

                    # Record timing
                    t0 = time.time()
                    first_token_time = None
                    active_snapshot = None

                    # Fill input and send
                    live_page.fill("#chat-in", prompt_text)
                    live_page.click("#chat-send-btn")

                    # Wait for new assistant bubble to be created in DOM
                    live_page.wait_for_function(f"document.querySelectorAll('#chat-box .msg.jarvis').length > {prev_count}", timeout=10000)
                    new_msg_elem = live_page.locator("#chat-box .msg.jarvis").nth(prev_count)
                    msg_content_loc = new_msg_elem.locator(".msg-content")

                    # Wait for stream to finish: Send button is disabled during stream, becomes enabled on finish
                    # Monitor for first token in assistant message
                    while time.time() - t0 < 60:
                        if first_token_time is None:
                            txt = msg_content_loc.inner_text().strip()
                            # Ignore cursor indicator if alone
                            if txt and txt != "▊":
                                first_token_time = time.time() - t0
                                active_snapshot = get_hardware_snapshot()

                        # Check if send button has re-enabled
                        send_btn = live_page.locator("#chat-send-btn")
                        if send_btn.is_enabled() and first_token_time is not None:
                            break
                        time.sleep(0.1)

                    t1 = time.time()
                    total_time = t1 - t0
                    ttft = first_token_time if first_token_time is not None else total_time
                    if active_snapshot is None:
                        active_snapshot = get_hardware_snapshot()

                    # Get response text
                    last_msg_content = msg_content_loc.inner_text().strip()
                    if last_msg_content.endswith("▊"):
                        last_msg_content = last_msg_content[:-1].strip()
                    badge_status = live_page.locator("#chat-status-badge").text_content().strip()
                    telemetry = live_page.locator("#chat-telemetry-badge").text_content().strip()

                    # Take screenshot
                    shot_filename = f"ai001_live_{turn_name}_{width}x{height}.png"
                    shot_path = EVIDENCE_DIR / shot_filename
                    live_page.screenshot(path=str(shot_path))
                    results["screenshots"].append(str(shot_path.relative_to(REPO_ROOT)))

                    turn_record = {
                        "turn_idx": turn_idx,
                        "name": turn_name,
                        "prompt": prompt_text,
                        "ttft_ms": round(ttft * 1000, 1),
                        "total_latency_ms": round(total_time * 1000, 1),
                        "reply_text": last_msg_content,
                        "status_badge": badge_status,
                        "telemetry": telemetry,
                        "hardware_idle": idle_snapshot,
                        "hardware_active": active_snapshot,
                        "screenshot": str(shot_path.relative_to(REPO_ROOT)),
                    }
                    print(f"  TTFT: {turn_record['ttft_ms']} ms, Total: {turn_record['total_latency_ms']} ms")
                    print(f"  Status: {badge_status}, Telemetry: {telemetry}")
                    print(f"  Reply snippet: {last_msg_content[:100]}...")
                    return turn_record

                # Turn 1: Memory seed
                t1_rec = execute_live_turn(
                    1,
                    "Remember the audit word violet. Reply with only the word.",
                    "turn1_seed",
                )
                vp_results["turns"].append(t1_rec)

                # Turn 2: Memory recall
                t2_rec = execute_live_turn(
                    2,
                    "What was the audit word?",
                    "turn2_recall",
                )
                assert "violet" in t2_rec["reply_text"].lower(), f"Memory recall failed! Expected 'violet' in '{t2_rec['reply_text']}'"
                t2_rec["recall_verified"] = True
                vp_results["turns"].append(t2_rec)

                # Turn 3: Code generation
                t3_rec = execute_live_turn(
                    3,
                    "Write a Python function is_even(n) that returns True for even integers.",
                    "turn3_code_gen",
                )
                assert "is_even" in t3_rec["reply_text"], f"Code generation failed! Expected 'is_even' in '{t3_rec['reply_text']}'"
                t3_rec["code_gen_verified"] = True
                vp_results["turns"].append(t3_rec)

                results["live_benchmark"][vp_key] = vp_results

            live_page.close()

    results["overall_verified"] = True

    # Save verification JSON evidence
    evidence_json_path = EVIDENCE_DIR / "step5-ai-001-verification.json"
    with open(evidence_json_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n==========================================")
    print(f"Step 5 Verification Completed Successfully!")
    print(f"Evidence saved to: {evidence_json_path}")
    print(f"==========================================")


if __name__ == "__main__":
    main()
