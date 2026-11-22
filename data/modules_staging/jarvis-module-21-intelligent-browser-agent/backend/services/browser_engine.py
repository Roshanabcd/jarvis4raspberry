"""Intelligent Browser Agent Engine (Module 21).

Enforces:
- Site allowlist/denylist policies and strict SSRF/private-IP blocking
- Mandatory human approval checkpoints before any form submission
- Multi-page workflow execution with mid-workflow approval pause/resume & cancellation
- Sandboxed download management with SHA-256 checksums
"""

from __future__ import annotations

import hashlib
import ipaddress
import json
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from backend.adapters.browser_adapter import (
    BrowserAutomationAdapter,
    SafeSimulatedBrowserAdapter,
    extract_dom,
)
from backend.app.config import BrowserAgentConfig
from backend.models.database import BrowserAgentDB, utc_now_iso

DEFAULT_POLICY: Dict[str, Any] = {
    "allowed_domains": ["docs.jarvis.local", "portal.jarvis.local", "releases.jarvis.local", "example.com"],
    "blocked_domains": ["localhost", "127.0.0.1", "0.0.0.0", "169.254.169.254"],
    "require_approval_for_form_submit": True,
    "allow_downloads": True,
}


class BrowserAgentError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}


class IntelligentBrowserEngine:
    def __init__(
        self,
        config: Optional[BrowserAgentConfig] = None,
        db: Optional[BrowserAgentDB] = None,
        adapter: Optional[BrowserAutomationAdapter] = None,
    ) -> None:
        self.config = config or BrowserAgentConfig.from_env()
        self.config.ensure_dirs()
        self.db = db or BrowserAgentDB(self.config.db_path)
        self.adapter = adapter or SafeSimulatedBrowserAdapter()
        self.downloads_root = Path(self.config.downloads_dir).resolve()
        self.downloads_root.mkdir(parents=True, exist_ok=True)
        self._started_at = time.monotonic()

        raw_pol = self.db.get_policy_raw("site_policy")
        self.policy: Dict[str, Any] = json.loads(raw_pol) if raw_pol else dict(DEFAULT_POLICY)

    # --- Site Permission & SSRF Policy ---
    def validate_url(self, url: str) -> str:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            raise BrowserAgentError("SCHEME_BLOCKED", f"URL scheme '{parsed.scheme}' is not permitted (only http/https).", 403)
        host = (parsed.hostname or "").lower()
        if not host:
            raise BrowserAgentError("INVALID_URL", "URL must contain a valid hostname.", 422)

        # Block raw private/loopback/link-local IPs (SSRF protection)
        try:
            ip = ipaddress.ip_address(host)
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
                raise BrowserAgentError("SSRF_BLOCKED", f"Private/loopback IP '{host}' is blocked by SSRF policy.", 403)
        except ValueError:
            pass

        if host in self.policy["blocked_domains"]:
            raise BrowserAgentError("DOMAIN_BLOCKED", f"Domain '{host}' is explicitly blocked by site policy.", 403)

        allowed = self.policy.get("allowed_domains", [])
        if allowed and not any(host == d or host.endswith("." + d) for d in allowed):
            raise BrowserAgentError(
                "DOMAIN_NOT_ALLOWLISTED",
                f"Domain '{host}' is not in the permitted site allowlist: {allowed}",
                403,
            )
        return url

    def update_policy(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        for k, v in updates.items():
            if k in self.policy and v is not None:
                self.policy[k] = v
        self.db.set_policy_raw("site_policy", json.dumps(self.policy))
        self.db.add_log("browser.policy.updated", "Updated site permission policy.")
        return dict(self.policy)

    # --- Session Management ---
    def create_session(self, name: str, start_url: str) -> Dict[str, Any]:
        self.validate_url(start_url)
        now = utc_now_iso()
        sid = f"bses_{uuid.uuid4().hex[:10]}"
        session = self.db.create_session(
            {
                "session_id": sid,
                "name": name,
                "current_url": start_url,
                "status": "active",
                "history": [start_url],
                "form_state": {},
                "created_at": now,
                "updated_at": now,
            }
        )
        self.db.add_log("browser.session.created", f"Created browser session '{name}' at {start_url}.", session_id=sid)
        return session

    def _require_session(self, session_id: str) -> Dict[str, Any]:
        s = self.db.get_session(session_id)
        if not s:
            raise BrowserAgentError("SESSION_NOT_FOUND", f"Browser session '{session_id}' not found", 404)
        if s["status"] != "active":
            raise BrowserAgentError("SESSION_CLOSED", f"Browser session '{session_id}' is closed", 409)
        return s

    def close_session(self, session_id: str) -> Dict[str, Any]:
        self._require_session(session_id)
        updated = self.db.update_session(session_id, status="closed")
        self.db.add_log("browser.session.closed", f"Closed browser session '{session_id}'.", session_id=session_id)
        return updated  # type: ignore[return-value]

    # --- Core Browser Operations ---
    def navigate(self, session_id: str, url: str) -> Dict[str, Any]:
        session = self._require_session(session_id)
        self.validate_url(url)
        page = self.adapter.fetch_page(url)
        dom = extract_dom(page["html"])
        history = list(session["history"]) + [url]
        self.db.update_session(session_id, current_url=url, history=history)
        self.db.add_log("browser.page.navigated", f"Navigated to {url} ({dom['title']}).", session_id=session_id)
        return {"session_id": session_id, "url": url, "status_code": page["status_code"], "simulated": page["simulated"], "dom": dom}

    def inspect_page(self, session_id: str) -> Dict[str, Any]:
        session = self._require_session(session_id)
        page = self.adapter.fetch_page(session["current_url"])
        dom = extract_dom(page["html"])
        return {"session_id": session_id, "url": session["current_url"], "simulated": page["simulated"], "dom": dom}

    def screenshot_and_analyze(self, session_id: str) -> Dict[str, Any]:
        session = self._require_session(session_id)
        page = self.adapter.fetch_page(session["current_url"])
        dom = extract_dom(page["html"])
        shot = self.adapter.capture_and_analyze_screenshot(session["current_url"], dom)
        self.db.add_log("browser.screenshot.analyzed", f"Captured & analyzed viewport for {session['current_url']}.", session_id=session_id)
        return {"session_id": session_id, "url": session["current_url"], **shot}

    def fill_form(self, session_id: str, form_id: str, fields: Dict[str, str]) -> Dict[str, Any]:
        session = self._require_session(session_id)
        fstate = dict(session["form_state"])
        fstate[form_id] = dict(fields)
        self.db.update_session(session_id, form_state=fstate)
        self.db.add_log("browser.form.filled", f"Filled form '{form_id}' with {len(fields)} field(s).", session_id=session_id)
        return {"session_id": session_id, "form_id": form_id, "fields": fields, "submitted": False}

    def request_form_submit(
        self,
        session_id: str,
        form_id: str,
        fields: Optional[Dict[str, str]] = None,
        requested_by: str = "operator",
        task_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        session = self._require_session(session_id)
        merged_fields = dict(session["form_state"].get(form_id, {}))
        if fields:
            merged_fields.update(fields)

        if self.policy.get("require_approval_for_form_submit", True):
            apr = self.db.create_approval(
                {
                    "approval_id": f"bap_{uuid.uuid4().hex[:10]}",
                    "session_id": session_id,
                    "task_id": task_id,
                    "url": session["current_url"],
                    "form_id": form_id,
                    "fields": merged_fields,
                    "prompt": f"Approve form submission '{form_id}' on {session['current_url']} requested by {requested_by}?",
                    "created_at": utc_now_iso(),
                }
            )
            self.db.add_log(
                "browser.form.awaiting_approval",
                f"Form '{form_id}' submission paused pending human approval ({apr['approval_id']}).",
                level="WARNING",
                session_id=session_id,
                task_id=task_id,
            )
            return {"status": "awaiting_approval", "approval": apr}

        res = self.adapter.submit_form(session["current_url"], form_id, merged_fields)
        self.db.add_log("browser.form.submitted", f"Submitted form '{form_id}' on {session['current_url']}.", session_id=session_id, task_id=task_id)
        return {"status": "submitted", "result": res}

    def download_file(self, session_id: str, url: str) -> Dict[str, Any]:
        self._require_session(session_id)
        if not self.policy.get("allow_downloads", True):
            raise BrowserAgentError("DOWNLOADS_DISABLED", "Downloads are disabled by site permission policy.", 403)
        self.validate_url(url)
        raw_name, data = self.adapter.fetch_download(url)
        safe_name = Path(raw_name).name or "download.bin"
        dest = (self.downloads_root / f"{uuid.uuid4().hex[:6]}_{safe_name}").resolve()
        dest.write_bytes(data)
        digest = hashlib.sha256(data).hexdigest()
        rec = self.db.record_download(
            {
                "download_id": f"dl_{uuid.uuid4().hex[:10]}",
                "session_id": session_id,
                "source_url": url,
                "filename": dest.name,
                "size_bytes": len(data),
                "sha256": digest,
                "simulated": self.adapter.is_simulated,
                "created_at": utc_now_iso(),
            }
        )
        self.db.add_log("browser.download.completed", f"Downloaded '{dest.name}' ({len(data)} bytes).", session_id=session_id)
        return rec

    # --- Multi-Page Workflow Runner ---
    def run_workflow(self, name: str, steps: List[Dict[str, Any]], session_id: Optional[str] = None, requested_by: str = "operator") -> Dict[str, Any]:
        if session_id:
            self._require_session(session_id)
            sid = session_id
        else:
            first_url = "https://docs.jarvis.local/overview"
            if steps and steps[0].get("action") == "navigate" and steps[0].get("params", {}).get("url"):
                first_url = str(steps[0]["params"]["url"])
            sid = self.create_session(f"Workflow: {name}", first_url)["session_id"]

        now = utc_now_iso()
        tid = f"bwf_{uuid.uuid4().hex[:10]}"
        task = self.db.create_task(
            {
                "task_id": tid,
                "session_id": sid,
                "name": name,
                "status": "running",
                "current_step": 0,
                "steps": steps,
                "results": [],
                "created_at": now,
                "updated_at": now,
            }
        )
        return self._advance_workflow(task["task_id"], requested_by=requested_by)

    def _advance_workflow(self, task_id: str, requested_by: str = "operator") -> Dict[str, Any]:
        task = self.db.get_task(task_id)
        assert task is not None
        results = list(task["results"])
        idx = int(task["current_step"])
        steps = task["steps"]
        sid = task["session_id"]

        while idx < len(steps):
            # Re-check cancellation
            latest = self.db.get_task(task_id)
            if latest and latest["status"] == "cancelled":
                return latest

            step = steps[idx]
            act = step["action"]
            p = step.get("params", {})
            try:
                if act == "navigate":
                    out = self.navigate(sid, str(p["url"]))
                elif act in ("inspect", "extract_dom"):
                    out = self.inspect_page(sid)
                elif act == "screenshot":
                    out = self.screenshot_and_analyze(sid)
                elif act == "fill_form":
                    out = self.fill_form(sid, str(p["form_id"]), dict(p.get("fields", {})))
                elif act == "submit_form":
                    out = self.request_form_submit(sid, str(p["form_id"]), p.get("fields"), requested_by=requested_by, task_id=task_id)
                    if out["status"] == "awaiting_approval":
                        results.append({"step": idx, "action": act, "status": "awaiting_approval", "approval_id": out["approval"]["approval_id"]})
                        return self.db.update_task(task_id, status="awaiting_approval", current_step=idx, results=results)  # type: ignore[return-value]
                elif act == "download":
                    out = self.download_file(sid, str(p["url"]))
                else:
                    raise BrowserAgentError("UNKNOWN_STEP", f"Unsupported workflow action '{act}'", 422)

                results.append({"step": idx, "action": act, "status": "completed", "output": out})
                idx += 1
            except BrowserAgentError as exc:
                self.db.add_log("browser.workflow.failed", f"Workflow '{task_id}' failed at step {idx}: {exc.message}", level="ERROR", session_id=sid, task_id=task_id)
                return self.db.update_task(task_id, status="failed", current_step=idx, results=results, error=exc.message)  # type: ignore[return-value]

        self.db.add_log("browser.workflow.completed", f"Workflow '{task['name']}' completed ({len(steps)} steps).", session_id=sid, task_id=task_id)
        return self.db.update_task(task_id, status="completed", current_step=idx, results=results)  # type: ignore[return-value]

    def decide_approval(self, approval_id: str, approved: bool, decided_by: str = "operator", comment: str = "") -> Dict[str, Any]:
        apr = self.db.get_approval(approval_id)
        if not apr:
            raise BrowserAgentError("APPROVAL_NOT_FOUND", f"Approval '{approval_id}' not found", 404)
        if apr["status"] != "pending":
            raise BrowserAgentError("APPROVAL_ALREADY_DECIDED", f"Approval '{approval_id}' already '{apr['status']}'", 409)

        status = "approved" if approved else "rejected"
        decided = self.db.decide_approval(approval_id, status, decided_by, comment)

        submission_result = None
        workflow_state = None
        if approved:
            submission_result = self.adapter.submit_form(apr["url"], apr["form_id"], apr["fields"])
            self.db.add_log("browser.form.submitted", f"Approved form '{apr['form_id']}' submitted by {decided_by}.", session_id=apr["session_id"], task_id=apr.get("task_id"))
            if apr.get("task_id"):
                t = self.db.get_task(apr["task_id"])
                if t and t["status"] == "awaiting_approval":
                    res = list(t["results"])
                    res.append({"step": t["current_step"], "action": "submit_form", "status": "completed", "output": submission_result})
                    self.db.update_task(t["task_id"], status="running", current_step=t["current_step"] + 1, results=res)
                    workflow_state = self._advance_workflow(t["task_id"], requested_by=decided_by)
        else:
            self.db.add_log("browser.form.rejected", f"Form '{apr['form_id']}' rejected by {decided_by}.", level="WARNING", session_id=apr["session_id"], task_id=apr.get("task_id"))
            if apr.get("task_id"):
                workflow_state = self.db.update_task(apr["task_id"], status="cancelled", error=f"Form submission rejected by {decided_by}")

        return {"approval": decided, "submission_result": submission_result, "workflow": workflow_state}

    def cancel_workflow(self, task_id: str) -> Dict[str, Any]:
        t = self.db.get_task(task_id)
        if not t:
            raise BrowserAgentError("TASK_NOT_FOUND", f"Workflow task '{task_id}' not found", 404)
        updated = self.db.update_task(task_id, status="cancelled", error="Cancelled by operator")
        self.db.add_log("browser.workflow.cancelled", f"Workflow '{task_id}' cancelled.", session_id=t["session_id"], task_id=task_id)
        return updated  # type: ignore[return-value]

    def get_status(self) -> Dict[str, Any]:
        return {
            "adapter": self.adapter.adapter_name,
            "simulated": self.adapter.is_simulated,
            "policy": self.policy,
            "sessions_count": len(self.db.list_sessions()),
            "tasks_count": len(self.db.list_tasks()),
            "pending_approvals": len(self.db.list_approvals(status="pending")),
            "downloads_count": len(self.db.list_downloads()),
            "uptime_seconds": round(time.monotonic() - self._started_at, 2),
        }
