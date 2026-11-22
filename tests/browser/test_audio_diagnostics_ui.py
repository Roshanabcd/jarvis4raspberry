"""
Playwright browser verification for Audio Diagnostics UI, Caption Formatting,
and Emergency Stop integrity on http://127.0.0.1:8000.
"""
import os
import sys
import unittest
from playwright.sync_api import sync_playwright

CHROME_BIN = "/usr/bin/google-chrome"


class TestAudioDiagnosticsUI(unittest.TestCase):
    """Browser checks verifying #estop-btn safety rail and caption formatting."""

    def setUp(self):
        self.playwright = sync_playwright().start()
        launch_kwargs = {
            "headless": True,
            "args": ["--no-sandbox", "--disable-dev-shm-usage", "--use-fake-ui-for-media-stream"],
        }
        if os.path.exists(CHROME_BIN):
            launch_kwargs["executable_path"] = CHROME_BIN
        self.browser = self.playwright.chromium.launch(**launch_kwargs)

    def tearDown(self):
        self.browser.close()
        self.playwright.stop()

    def test_estop_button_and_caption_rendering(self):
        """Assert #estop-btn is visible and enabled (never clicked), and captions preserve newlines."""
        errors = []
        page = self.browser.new_page(viewport={"width": 1440, "height": 900})
        page.on("pageerror", lambda exc: errors.append(str(exc)))

        # Load Dashboard
        response = page.goto("http://127.0.0.1:8000/", timeout=15000)
        self.assertIsNotNone(response)
        self.assertEqual(response.status, 200)

        # 1. HARD SAFETY RAIL: #estop-btn must be visible and enabled (NEVER CLICK IT)
        estop = page.locator("#estop-btn")
        self.assertTrue(estop.is_visible())
        self.assertTrue(estop.is_enabled())

        # 2. Assert zero unhandled JavaScript errors during initial load
        self.assertEqual(len(errors), 0, f"Page had unhandled errors: {errors}")

        # 3. Check Caption and Control Center elements
        caption = page.locator("#cc-caption")
        self.assertTrue(caption.is_visible())

        # 4. Inject a multi-line formatted message into the chat and test syncConversation formatting
        page.evaluate("""() => {
            const chatBox = document.getElementById('chat-box');
            if (chatBox) {
                const msg = document.createElement('div');
                msg.className = 'msg jarvis';
                msg.innerHTML = '<span class="msg-author">JARVIS</span><div class="msg-content">Line 1: Audio Diagnostics<br>Line 2: Master Sink Active<br>Line 3: Recommendations</div>';
                chatBox.appendChild(msg);
            }
        }""")

        page.wait_for_timeout(500)

        # Verify #cc-conversation received the message with linebreaks preserved
        cc_conv_text = page.locator("#cc-conversation").inner_text()
        self.assertIn("Line 1: Audio Diagnostics", cc_conv_text)
        self.assertIn("Line 2: Master Sink Active", cc_conv_text)
        self.assertIn("\n", cc_conv_text, "Lines must not be collapsed into a single line")

        # Verify #cc-caption received the latest text with linebreaks intact
        caption_text = page.locator("#cc-caption").inner_text()
        self.assertIn("Line 1: Audio Diagnostics", caption_text)
        self.assertIn("Line 2: Master Sink Active", caption_text)

        # Verify css white-space on #cc-caption is pre-wrap
        white_space = page.eval_on_selector("#cc-caption", "el => window.getComputedStyle(el).whiteSpace")
        self.assertEqual(white_space, "pre-wrap")

        # Verify #estop-btn remained untouched and enabled throughout
        self.assertTrue(estop.is_visible())
        self.assertTrue(estop.is_enabled())


if __name__ == "__main__":
    unittest.main()
