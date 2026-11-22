"""Publishing bridge supporting webhook automation and manual packet export fallback."""

from __future__ import annotations

import asyncio
import json
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from .config import SocialAutomationConfig


class SocialPublisher:
    """Dispatches scheduled social posts via webhook or writes a ready-to-post manual bundle."""

    def __init__(self, config: SocialAutomationConfig) -> None:
        self.config = config

    async def publish(
        self,
        post: Dict[str, Any],
        dry_run: bool = True,
    ) -> Tuple[str, str, Optional[str], str]:
        """Return (status, publish_mode, export_path, message)."""
        if dry_run:
            return (
                post["status"],
                f"dry-run ({self.config.publish_mode_label()})",
                None,
                f"Dry-run OK for post #{post['id']} ({post['platform']}). No external publish performed.",
            )

        if self.config.publish_webhook_url:
            ok, msg = await asyncio.to_thread(self._dispatch_webhook_sync, post)
            if ok:
                return ("published", "webhook-bridge", None, msg)
            # Fall back to manual export so nothing is lost
            export_path = self._write_manual_export(post)
            return (
                "published",
                "manual-export-fallback",
                str(export_path),
                f"Webhook failed ({msg}); exported ready-to-post packet to {export_path.name}.",
            )

        export_path = self._write_manual_export(post)
        return (
            "published",
            "manual-export-fallback",
            str(export_path),
            f"Exported ready-to-post packet to {export_path.name} (set JARVIS_SOCIAL_WEBHOOK_URL for live bridge).",
        )

    def _dispatch_webhook_sync(self, post: Dict[str, Any]) -> Tuple[bool, str]:
        payload = json.dumps(
            {
                "post_id": post["id"],
                "campaign_name": post["campaign_name"],
                "platform": post["platform"],
                "title": post["title"],
                "copy_text": post["copy_text"],
                "hashtags": post["hashtags"],
                "scheduled_for": post["scheduled_for"],
            }
        ).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self.config.publish_webhook_token:
            headers["Authorization"] = f"Bearer {self.config.publish_webhook_token}"
        req = urllib.request.Request(
            self.config.publish_webhook_url,
            data=payload,
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.config.request_timeout_sec) as resp:
                return (200 <= resp.status < 300, f"Webhook accepted with HTTP {resp.status}.")
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            return (False, str(exc))

    def _write_manual_export(self, post: Dict[str, Any]) -> Path:
        export_dir = Path(self.config.manual_export_dir)
        export_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        plat_slug = "".join(ch for ch in post["platform"].lower() if ch.isalnum()) or "social"
        out_path = export_dir / f"post_{post['id']}_{plat_slug}_{stamp}.md"
        hashtags_str = " ".join(post["hashtags"])
        md = (
            f"# Ready-to-Publish Social Post (#{post['id']})\n\n"
            f"- **Platform:** {post['platform']}\n"
            f"- **Campaign:** {post['campaign_name']}\n"
            f"- **Title:** {post['title']}\n"
            f"- **Scheduled For (UTC):** {post['scheduled_for']}\n\n"
            f"## Copy\n\n{post['copy_text']}\n\n"
            f"## Hashtags\n\n{hashtags_str}\n"
        )
        out_path.write_text(md, encoding="utf-8")
        return out_path
