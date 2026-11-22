"""
JARVIS OS — Antigravity IDE Automation & Auto-Approver Service
Monitors running Antigravity conversations, auto-selects Option 1, sends confirmations,
and manages Antigravity execution settings.
"""

import os
import json
import time
import logging
import asyncio
import threading
from typing import Dict, Any, List, Optional
from pathlib import Path

logger = logging.getLogger("jarvis.antigravity_approver")

GEMINI_CONFIG_DIR = Path.home() / ".gemini" / "config"
CONFIG_JSON_PATH = GEMINI_CONFIG_DIR / "config.json"
HOOKS_JSON_PATH = GEMINI_CONFIG_DIR / "hooks.json"
PROJECTS_DIR = GEMINI_CONFIG_DIR / "projects"
OUTSIDE_PROJECT_PATH = PROJECTS_DIR / "outside-of-project.json"
DEFAULT_CLI_PROJECT_PATH = PROJECTS_DIR / "default-cli-project.json"


def apply_antigravity_settings() -> Dict[str, Any]:
    """
    Applies Antigravity settings so commands auto-execute without asking:
    1. autoExecutionPolicy = CASCADE_COMMANDS_AUTO_EXECUTION_EAGER in config.json
    2. autoExecutionPolicy = CASCADE_COMMANDS_AUTO_EXECUTION_EAGER in outside-of-project.json & default-cli-project.json
    3. Lifecycle PreToolUse hook in hooks.json returning {"decision": "allow"}
    """
    applied = []
    errors = []

    # 1. Update config.json
    try:
        if CONFIG_JSON_PATH.exists():
            with open(CONFIG_JSON_PATH, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            if "userSettings" not in cfg:
                cfg["userSettings"] = {}
            cfg["userSettings"]["autoExecutionPolicy"] = "CASCADE_COMMANDS_AUTO_EXECUTION_EAGER"
            with open(CONFIG_JSON_PATH, "w", encoding="utf-8") as f:
                json.dump(cfg, f, indent=2)
            applied.append("config.json: autoExecutionPolicy set to CASCADE_COMMANDS_AUTO_EXECUTION_EAGER")
    except Exception as e:
        logger.error(f"Error updating config.json: {e}")
        errors.append(f"config.json: {e}")

    # 2. Update project configs
    for proj_path in [OUTSIDE_PROJECT_PATH, DEFAULT_CLI_PROJECT_PATH]:
        try:
            if proj_path.exists():
                with open(proj_path, "r", encoding="utf-8") as f:
                    pcfg = json.load(f)
                if "settings" not in pcfg:
                    pcfg["settings"] = {}
                pcfg["settings"]["autoExecutionPolicy"] = "CASCADE_COMMANDS_AUTO_EXECUTION_EAGER"
                with open(proj_path, "w", encoding="utf-8") as f:
                    json.dump(pcfg, f, indent=2)
                applied.append(f"{proj_path.name}: autoExecutionPolicy set to CASCADE_COMMANDS_AUTO_EXECUTION_EAGER")
        except Exception as e:
            logger.error(f"Error updating {proj_path}: {e}")
            errors.append(f"{proj_path.name}: {e}")

    # 3. Ensure hooks.json has PreToolUse auto-allow
    try:
        hook_payload = {
            "jarvis-auto-approve": {
                "PreToolUse": [
                    {
                        "matcher": "*",
                        "hooks": [
                            {
                                "type": "command",
                                "command": "echo '{\"decision\": \"allow\", \"reason\": \"Auto-allowed by JARVIS\"}'"
                            }
                        ]
                    }
                ]
            }
        }
        with open(HOOKS_JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(hook_payload, f, indent=2)
        applied.append("hooks.json: PreToolUse wildcard auto-allow hook installed")
    except Exception as e:
        logger.error(f"Error creating hooks.json: {e}")
        errors.append(f"hooks.json: {e}")

    return {
        "success": len(errors) == 0,
        "applied": applied,
        "errors": errors,
        "timestamp": time.time()
    }


async def scan_and_auto_approve_cdp(cdp_port: int = 9333, max_pages: int = 5) -> Dict[str, Any]:
    """
    Connects to Antigravity IDE over CDP (default port 9333), inspects open conversation pages,
    and if an interactive prompt or confirmation modal is open:
    - Selects Option 1 (first radio/choice)
    - Clicks Submit / Send / Allow
    """
    actions = []
    from playwright.async_api import async_playwright

    try:
        async with async_playwright() as p:
            try:
                browser = await p.chromium.connect_over_cdp(f"http://127.0.0.1:{cdp_port}")
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Cannot connect to Antigravity CDP on port {cdp_port}: {e}",
                    "actions": []
                }

            for ctx in browser.contexts:
                for page in ctx.pages[:max_pages]:
                    try:
                        title = await page.title()
                        url = page.url

                        # Strategy A: Check for radio options (e.g. ask_question modal: option 1, 2, 3...)
                        radios = await page.locator('input[type="radio"], [role="radio"]').all()
                        if radios:
                            first_radio = radios[0]
                            # Check if first option is already checked or needs checking
                            is_checked = False
                            try:
                                is_checked = await first_radio.is_checked()
                            except Exception:
                                aria = await first_radio.get_attribute("aria-checked")
                                is_checked = (aria == "true")

                            if not is_checked:
                                try:
                                    await first_radio.check(force=True)
                                except Exception:
                                    await first_radio.click(force=True)
                                logger.info(f"Selected Option 1 in '{title}'")

                            # Look for Submit / Send button
                            submit_btn = None
                            for btn in await page.locator('button').all():
                                try:
                                    txt = (await btn.text_content() or "").strip()
                                    if any(s in txt.lower() for s in ["submit", "send"]):
                                        if await btn.is_visible() and await btn.is_enabled():
                                            submit_btn = btn
                                            break
                                except Exception:
                                    pass

                            if submit_btn:
                                await submit_btn.click()
                                actions.append({
                                    "target": "question_modal",
                                    "page": title,
                                    "url": url,
                                    "action": "selected_option_1_and_submitted",
                                    "timestamp": time.time()
                                })
                                logger.info(f"Submitted Option 1 in '{title}'")
                                continue

                        # Strategy B: Check for command execution permission buttons ("Send" / "Allow" vs "Skip")
                        allow_btn = None
                        skip_btn = None
                        for btn in await page.locator('button').all():
                            try:
                                txt = (await btn.text_content() or "").strip()
                                if txt in ["Send", "Allow", "Proceed", "Run"]:
                                    if await btn.is_visible() and await btn.is_enabled():
                                        allow_btn = btn
                                elif txt in ["Skip", "Cancel", "Deny"]:
                                    skip_btn = btn
                            except Exception:
                                pass

                        # If both Allow/Send and Skip are present, this is the command permission prompt!
                        if allow_btn and skip_btn:
                            btn_text = (await allow_btn.text_content() or "").strip()
                            await allow_btn.click()
                            actions.append({
                                "target": "command_permission_prompt",
                                "page": title,
                                "url": url,
                                "action": f"clicked_{btn_text}_(Option 1)",
                                "timestamp": time.time()
                            })
                            logger.info(f"Clicked {btn_text} (Option 1) in '{title}'")

                    except Exception as e:
                        logger.warning(f"Error inspecting page in Antigravity: {e}")

            # Disconnect cleanly without closing Antigravity IDE
            try:
                # Do not call browser.close() as it may terminate the remote browser session
                # Playwright's async context manager handles disconnection on exit
                pass
            except Exception:
                pass

        return {
            "success": True,
            "actions": actions,
            "count": len(actions)
        }

    except Exception as e:
        logger.error(f"scan_and_auto_approve_cdp error: {e}")
        return {
            "success": False,
            "error": str(e),
            "actions": []
        }


class AntigravitySupervisorDaemon:
    """
    Background supervisor that periodically checks Antigravity IDE
    and automatically accepts Option 1 and sends confirmations.
    """
    _instance: Optional["AntigravitySupervisorDaemon"] = None

    def __init__(self, cdp_port: int = 9333, poll_interval: float = 1.5):
        self.cdp_port = cdp_port
        self.poll_interval = poll_interval
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._total_approvals = 0
        self._last_action: Optional[Dict[str, Any]] = None
        self._lock = threading.Lock()

    @classmethod
    def get_instance(cls) -> "AntigravitySupervisorDaemon":
        if cls._instance is None:
            cls._instance = AntigravitySupervisorDaemon()
        return cls._instance

    def start(self) -> Dict[str, Any]:
        with self._lock:
            if self._running:
                return {"status": "already_running", "total_approvals": self._total_approvals}
            self._running = True
            self._thread = threading.Thread(target=self._run_loop, daemon=True, name="AntigravitySupervisor")
            self._thread.start()
            logger.info("AntigravitySupervisorDaemon started.")
            return {"status": "started", "poll_interval": self.poll_interval}

    def stop(self) -> Dict[str, Any]:
        with self._lock:
            if not self._running:
                return {"status": "already_stopped"}
            self._running = False
            logger.info("AntigravitySupervisorDaemon stopping...")
            return {"status": "stopped", "total_approvals": self._total_approvals}

    def is_running(self) -> bool:
        return self._running

    def get_status(self) -> Dict[str, Any]:
        return {
            "running": self._running,
            "poll_interval": self.poll_interval,
            "cdp_port": self.cdp_port,
            "total_approvals": self._total_approvals,
            "last_action": self._last_action,
            "settings_applied": True
        }

    def _run_loop(self):
        # Dedicated event loop for async Playwright in this background thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        logger.info("Antigravity supervisor loop entered.")

        while self._running:
            try:
                result = loop.run_until_complete(scan_and_auto_approve_cdp(self.cdp_port))
                actions = result.get("actions", [])
                if actions:
                    with self._lock:
                        self._total_approvals += len(actions)
                        self._last_action = actions[-1]
            except Exception as e:
                logger.debug(f"Supervisor poll cycle error: {e}")

            time.sleep(self.poll_interval)

        loop.close()
        logger.info("Antigravity supervisor loop exited.")


# Singleton supervisor instance
antigravity_supervisor = AntigravitySupervisorDaemon.get_instance()
