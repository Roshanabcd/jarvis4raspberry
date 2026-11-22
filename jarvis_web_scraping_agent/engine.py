"""Core Autonomous Web Scraping Agent engine: extraction, change monitoring, and diffing."""

from __future__ import annotations

import asyncio
import difflib
from typing import Optional

from .config import WebScraperConfig
from .models import (
    ChangeCheckResponse,
    CreateMonitorRequest,
    ExtractedPage,
    ExtractRequest,
    LinkItem,
    MonitorRecord,
)
from .parser import parse_html_structure
from .policy import ScrapePolicyGuard
from .storage import WebScraperStore


class WebScraperEngine:
    """Orchestrates policy-compliant extraction, HTML parsing, and scheduled change monitoring."""

    def __init__(
        self,
        config: WebScraperConfig,
        policy: ScrapePolicyGuard,
        store: WebScraperStore,
    ) -> None:
        self.config = config
        self.policy = policy
        self.store = store

    async def extract(self, req: ExtractRequest) -> ExtractedPage:
        if req.raw_html is not None and req.raw_html.strip():
            html = req.raw_html
            source = req.url or "raw-html"
            robots_allowed = True
        elif req.url:
            html, robots_allowed = await asyncio.to_thread(self.policy.fetch_html_sync, req.url)
            source = req.url
        else:
            raise ValueError("Provide either 'url' or 'raw_html' to extract.")

        parsed = parse_html_structure(html, base_url=req.url or "", target_tag=req.target_tag)
        snap_id: Optional[int] = None
        if req.save_snapshot:
            snap_id = self.store.save_snapshot(
                source=source,
                title=parsed["title"] or source,
                content_hash=parsed["content_hash"],
                word_count=parsed["word_count"],
                payload=parsed,
            )

        return ExtractedPage(
            snapshot_id=snap_id,
            source=source,
            content_hash=parsed["content_hash"],
            title=parsed["title"],
            meta_description=parsed["meta_description"],
            headings=parsed["headings"],
            links=[LinkItem(**l) for l in parsed["links"]],
            tables=parsed["tables"],
            targeted_elements=parsed["targeted_elements"],
            text_preview=parsed["text_preview"],
            word_count=parsed["word_count"],
            robots_allowed=robots_allowed,
        )

    def create_monitor(self, req: CreateMonitorRequest) -> MonitorRecord:
        self.policy.validate_url(req.url)
        row = self.store.create_monitor(
            name=req.name,
            url=req.url,
            target_tag=req.target_tag,
            interval_minutes=req.interval_minutes,
        )
        return MonitorRecord(**row)

    async def check_monitor(
        self,
        monitor_id: int,
        raw_html_override: Optional[str] = None,
    ) -> ChangeCheckResponse:
        mon = self.store.get_monitor(monitor_id)
        if not mon:
            raise KeyError(f"Monitor {monitor_id} not found.")

        if raw_html_override is not None:
            html = raw_html_override
        else:
            html, _ = await asyncio.to_thread(self.policy.fetch_html_sync, str(mon["url"]))

        parsed = parse_html_structure(html, base_url=str(mon["url"]), target_tag=mon.get("target_tag"))
        prev_hash: Optional[str] = mon.get("last_hash")
        prev_text: str = mon.get("last_text") or ""
        curr_hash = str(parsed["content_hash"])
        curr_text = str(parsed["full_text"])

        changed = prev_hash is not None and prev_hash != curr_hash
        diff_lines = difflib.unified_diff(
            prev_text.splitlines(),
            curr_text.splitlines(),
            fromfile="previous",
            tofile="current",
            lineterm="",
        )
        unified_diff = "\n".join(diff_lines) if changed else ""

        snap_id = self.store.save_snapshot(
            source=str(mon["url"]),
            title=parsed["title"] or str(mon["name"]),
            content_hash=curr_hash,
            word_count=parsed["word_count"],
            payload={**parsed, "changed": changed, "unified_diff": unified_diff},
            monitor_id=monitor_id,
            changed=changed,
        )
        self.store.update_monitor_check(monitor_id, curr_hash, curr_text, changed)

        return ChangeCheckResponse(
            monitor_id=monitor_id,
            monitor_name=str(mon["name"]),
            url=str(mon["url"]),
            snapshot_id=snap_id,
            changed=changed,
            previous_hash=prev_hash,
            current_hash=curr_hash,
            unified_diff=unified_diff,
            word_count=parsed["word_count"],
        )
