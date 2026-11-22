"""Core AI Social Media Automation engine: planning, copy generation, scheduling, publishing, and analytics."""

from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from .config import SocialAutomationConfig
from .llm_provider import SocialLLMClient
from .models import (
    AnalyticsSummaryResponse,
    CreatePostRequest,
    PlanCampaignRequest,
    PlanCampaignResponse,
    PlatformAnalytics,
    PublishResult,
    RecordMetricsRequest,
    RunDueResponse,
    SocialPostRecord,
)
from .publisher import SocialPublisher
from .storage import SocialAutomationStore

PLATFORM_LIMITS: Dict[str, int] = {
    "x": 280,
    "twitter": 280,
    "linkedin": 3000,
    "instagram": 2200,
    "youtube": 2000,
}

DAY_ANGLES: List[str] = [
    "Problem & Hook",
    "Architecture Deep-Dive",
    "Behind-the-Scenes Build Log",
    "Lessons Learned & Benchmarks",
    "Live Demo & Call to Action",
    "Community Q&A Prompt",
    "Weekly Recap & Roadmap",
]


def _extract_hashtags(topic: str) -> List[str]:
    stop = {"the", "and", "for", "with", "how", "why", "into", "from", "your", "building", "about"}
    words = re.findall(r"[A-Za-z0-9]+", topic)
    tags: List[str] = []
    for w in words:
        if len(w) >= 3 and w.lower() not in stop:
            tag = "#" + w[0].upper() + w[1:]
            if tag not in tags:
                tags.append(tag)
    for default in ("#JARVISOS", "#AI", "#BuildInPublic"):
        if default not in tags:
            tags.append(default)
    return tags[:5]


def _fit_platform_limit(platform: str, text: str) -> str:
    limit = PLATFORM_LIMITS.get(platform.lower(), 2000)
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


class SocialAutomationEngine:
    """Coordinates campaign planning, copy generation, scheduled publishing, and analytics."""

    def __init__(
        self,
        config: SocialAutomationConfig,
        store: SocialAutomationStore,
        llm: SocialLLMClient,
        publisher: SocialPublisher,
    ) -> None:
        self.config = config
        self.store = store
        self.llm = llm
        self.publisher = publisher

    async def plan_campaign(self, req: PlanCampaignRequest) -> PlanCampaignResponse:
        if req.start_iso_utc:
            start_dt = datetime.fromisoformat(req.start_iso_utc.replace("Z", "+00:00"))
            if start_dt.tzinfo is None:
                start_dt = start_dt.replace(tzinfo=timezone.utc)
        else:
            start_dt = datetime.now(timezone.utc) + timedelta(hours=1)

        system_prompt = (
            "You are a social media strategist inside JARVIS OS. Return ONLY a JSON array of post objects, "
            'each with keys: "day" (int), "platform" (str), "title" (str), "copy_text" (str), "hashtags" (list of str).'
        )
        user_prompt = (
            f"Campaign: {req.campaign_name}\n"
            f"Topic: {req.topic}\n"
            f"Platforms: {', '.join(req.platforms)}\n"
            f"Days: {req.days}\n"
            f"Tone: {req.tone}\n"
            f"CTA: {req.call_to_action}\n"
            "Keep X/Twitter copy under 280 characters."
        )

        res = await self.llm.complete(system_prompt, user_prompt)
        drafts = self._parse_llm_plan(res.text) if (not res.used_fallback and res.text) else []

        if not drafts:
            drafts = self._offline_plan(req)

        created_posts: List[SocialPostRecord] = []
        for idx, item in enumerate(drafts):
            day_offset = max(0, int(item.get("day", idx + 1)) - 1)
            plat = str(item.get("platform") or req.platforms[idx % len(req.platforms)])
            title = str(item.get("title") or f"{req.campaign_name} — Day {day_offset + 1}")
            copy_text = _fit_platform_limit(plat, str(item.get("copy_text") or req.topic))
            raw_tags = item.get("hashtags")
            hashtags = [str(t) for t in raw_tags] if isinstance(raw_tags, list) else _extract_hashtags(req.topic)

            sched_dt = start_dt + timedelta(days=day_offset, hours=(idx % len(req.platforms)) * 2)
            row = self.store.create_post(
                campaign_name=req.campaign_name,
                platform=plat,
                title=title,
                copy_text=copy_text,
                hashtags=hashtags,
                scheduled_for=sched_dt.isoformat(),
                status="scheduled",
            )
            created_posts.append(SocialPostRecord(**row))

        return PlanCampaignResponse(
            campaign_name=req.campaign_name,
            provider_used=res.provider_used,
            posts_created=len(created_posts),
            posts=created_posts,
            manual_prompt_fallback=res.manual_prompt_fallback,
        )

    @staticmethod
    def _parse_llm_plan(text: str) -> List[Dict[str, object]]:
        match = re.search(r"\[.*\]", text, re.DOTALL)
        if not match:
            return []
        try:
            data = json.loads(match.group(0))
            if isinstance(data, list):
                return [item for item in data if isinstance(item, dict)]
        except json.JSONDecodeError:
            return []
        return []

    @staticmethod
    def _offline_plan(req: PlanCampaignRequest) -> List[Dict[str, object]]:
        tags = _extract_hashtags(req.topic)
        out: List[Dict[str, object]] = []
        for day in range(1, req.days + 1):
            angle = DAY_ANGLES[(day - 1) % len(DAY_ANGLES)]
            for plat in req.platforms:
                p_low = plat.lower()
                if p_low in ("x", "twitter"):
                    copy = f"Day {day} ({angle}): {req.topic.strip()} — built clean and modular. {req.call_to_action} {' '.join(tags[:2])}"
                elif "linkedin" in p_low:
                    copy = (
                        f"Day {day} — {angle}: {req.topic.strip()}\n\n"
                        f"We are building this in a {req.tone} workflow with strict modular isolation, "
                        f"automated verification, and lightweight local execution.\n\n"
                        f"{req.call_to_action}\n\n{' '.join(tags)}"
                    )
                elif "instagram" in p_low:
                    copy = f"{angle}: {req.topic.strip()} — swipe/watch to see today's build milestone.\n\n{req.call_to_action}\n{' '.join(tags)}"
                else:
                    copy = f"[{angle}] {req.topic.strip()} — full breakdown and progress update. {req.call_to_action} {' '.join(tags[:4])}"

                out.append(
                    {
                        "day": day,
                        "platform": plat,
                        "title": f"Day {day}: {angle} ({plat})",
                        "copy_text": _fit_platform_limit(plat, copy),
                        "hashtags": tags,
                    }
                )
        return out

    def create_post(self, req: CreatePostRequest) -> SocialPostRecord:
        sched = req.scheduled_for or (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        copy_text = _fit_platform_limit(req.platform, req.copy_text)
        row = self.store.create_post(
            campaign_name=req.campaign_name,
            platform=req.platform,
            title=req.title,
            copy_text=copy_text,
            hashtags=req.hashtags,
            scheduled_for=sched,
            status=req.status,
        )
        return SocialPostRecord(**row)

    async def publish_post(self, post_id: int, dry_run: bool = True) -> PublishResult:
        post = self.store.get_post(post_id)
        if not post:
            raise KeyError(f"Post {post_id} not found.")
        status, mode, export_path, msg = await self.publisher.publish(post, dry_run=dry_run)
        if not dry_run:
            self.store.mark_published(post_id, status=status, publish_mode=mode, export_path=export_path)
        return PublishResult(
            post_id=post_id,
            platform=post["platform"],
            dry_run=dry_run,
            status=status,
            publish_mode=mode,
            export_path=export_path,
            message=msg,
        )

    async def run_due_queue(self, dry_run: bool = True) -> RunDueResponse:
        now_iso = datetime.now(timezone.utc).isoformat()
        due_posts = self.store.list_due_posts(now_iso)
        results: List[PublishResult] = []
        for post in due_posts:
            res = await self.publish_post(int(post["id"]), dry_run=dry_run)
            results.append(res)
        return RunDueResponse(
            checked_at_utc=now_iso,
            dry_run=dry_run,
            due_count=len(due_posts),
            results=results,
        )

    def record_metrics(self, post_id: int, req: RecordMetricsRequest) -> SocialPostRecord:
        updated = self.store.update_metrics(
            post_id=post_id,
            impressions=req.impressions,
            likes=req.likes,
            comments=req.comments,
            shares=req.shares,
            clicks=req.clicks,
        )
        if not updated:
            raise KeyError(f"Post {post_id} not found.")
        return SocialPostRecord(**updated)

    def get_analytics(self) -> AnalyticsSummaryResponse:
        posts = self.store.list_posts(limit=500)
        scheduled_count = sum(1 for p in posts if p["status"] == "scheduled")
        published_count = sum(1 for p in posts if p["status"] == "published")

        total_imp = sum(int(p["impressions"]) for p in posts)
        total_clicks = sum(int(p["clicks"]) for p in posts)
        total_eng = sum(
            int(p["likes"]) + int(p["comments"]) + int(p["shares"]) + int(p["clicks"])
            for p in posts
        )

        overall_er = round((total_eng / total_imp) * 100.0, 2) if total_imp > 0 else 0.0
        overall_ctr = round((total_clicks / total_imp) * 100.0, 2) if total_imp > 0 else 0.0

        grouped: Dict[str, List[Dict[str, object]]] = {}
        for p in posts:
            grouped.setdefault(str(p["platform"]), []).append(p)

        by_platform: List[PlatformAnalytics] = []
        for plat, items in sorted(grouped.items()):
            imp = sum(int(i["impressions"]) for i in items)
            clk = sum(int(i["clicks"]) for i in items)
            eng = sum(int(i["likes"]) + int(i["comments"]) + int(i["shares"]) + int(i["clicks"]) for i in items)
            pub = sum(1 for i in items if i["status"] == "published")
            by_platform.append(
                PlatformAnalytics(
                    platform=plat,
                    posts_count=len(items),
                    published_count=pub,
                    impressions=imp,
                    engagements=eng,
                    clicks=clk,
                    engagement_rate_pct=round((eng / imp) * 100.0, 2) if imp > 0 else 0.0,
                    ctr_pct=round((clk / imp) * 100.0, 2) if imp > 0 else 0.0,
                )
            )

        sorted_top = sorted(
            posts,
            key=lambda p: (
                int(p["likes"]) + int(p["comments"]) + int(p["shares"]) + int(p["clicks"]),
                int(p["impressions"]),
            ),
            reverse=True,
        )[:5]

        return AnalyticsSummaryResponse(
            total_posts=len(posts),
            scheduled_count=scheduled_count,
            published_count=published_count,
            total_impressions=total_imp,
            total_engagements=total_eng,
            total_clicks=total_clicks,
            overall_engagement_rate_pct=overall_er,
            overall_ctr_pct=overall_ctr,
            by_platform=by_platform,
            top_posts=[SocialPostRecord(**p) for p in sorted_top],
        )
