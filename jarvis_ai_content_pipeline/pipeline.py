"""Core AI Content Creation Pipeline engine: blogs, short-video scripts, hooks/captions, carousels, and campaigns."""

from __future__ import annotations

import math
import re
from typing import List, Tuple

from .config import ContentPipelineConfig
from .llm_provider import ContentLLMClient
from .models import (
    BlogRequest,
    BlogResponse,
    CampaignRequest,
    CampaignResponse,
    CarouselRequest,
    CarouselResponse,
    CarouselSlide,
    HookItem,
    HooksCaptionsRequest,
    HooksCaptionsResponse,
    PlatformCaption,
    VideoScene,
    VideoScriptRequest,
    VideoScriptResponse,
    model_to_dict,
)
from .storage import ContentPipelineStore


def _extract_tags(topic: str, extra: List[str] | None = None) -> List[str]:
    stop = {
        "the", "and", "for", "with", "how", "why", "into", "from", "your",
        "this", "that", "using", "build", "building", "guide", "about",
    }
    words = re.findall(r"[A-Za-z0-9]+", topic.lower())
    tags: List[str] = []
    for w in words:
        if len(w) >= 3 and w not in stop and w not in tags:
            tags.append(w)
    for item in extra or []:
        clean = re.sub(r"[^a-zA-Z0-9]", "", item.lower())
        if clean and clean not in tags:
            tags.append(clean)
    return tags[:8] or ["tech", "ai", "jarvis"]


def _estimate_read_minutes(text: str) -> int:
    words = len(text.split())
    return max(1, math.ceil(words / 200))


class ContentPipelineEngine:
    """Generates and persists technical blogs, video scripts, hooks/captions, carousels, and campaigns."""

    def __init__(
        self,
        config: ContentPipelineConfig,
        store: ContentPipelineStore,
        llm: ContentLLMClient,
    ) -> None:
        self.config = config
        self.store = store
        self.llm = llm

    async def generate_blog(self, req: BlogRequest) -> BlogResponse:
        system_prompt = (
            "You are a senior technical writer inside JARVIS OS. "
            "Write a clean, well-structured Markdown technical blog post with clear headings, "
            "practical steps, concrete architecture notes, and a concise summary."
        )
        points_block = "\n".join(f"- {p}" for p in req.key_points) if req.key_points else "- Practical implementation"
        user_prompt = (
            f"Topic: {req.topic}\n"
            f"Target audience: {req.audience}\n"
            f"Tone: {req.tone}\n"
            f"Target word count: ~{req.target_words}\n"
            f"Include code example: {req.include_code_example}\n"
            f"Key points to cover:\n{points_block}\n"
        )

        res = await self.llm.complete(system_prompt, user_prompt)
        tags = _extract_tags(req.topic, ["jarvis", "engineering"])

        if not res.used_fallback and res.text:
            markdown = res.text.strip()
            first_heading = next(
                (line.lstrip("# ").strip() for line in markdown.splitlines() if line.startswith("#")),
                req.topic.strip(),
            )
            title = first_heading[:140]
            meta = f"Practical technical guide on {req.topic.strip()} for {req.audience}."
        else:
            title, meta, markdown = self._offline_blog(req, tags)

        read_mins = _estimate_read_minutes(markdown)
        item_id = self.store.save_item(
            content_type="blog",
            title=title,
            topic=req.topic,
            provider=res.provider_used,
            markdown=markdown,
            payload={
                "title": title,
                "meta_description": meta,
                "estimated_read_minutes": read_mins,
                "tags": tags,
            },
        )

        return BlogResponse(
            item_id=item_id,
            provider_used=res.provider_used,
            title=title,
            meta_description=meta,
            estimated_read_minutes=read_mins,
            tags=tags,
            markdown=markdown,
            manual_prompt_fallback=res.manual_prompt_fallback,
        )

    @staticmethod
    def _offline_blog(req: BlogRequest, tags: List[str]) -> Tuple[str, str, str]:
        title = f"{req.topic.strip()}: Practical Architecture & Implementation Guide"
        meta = f"Step-by-step technical guide to {req.topic.strip()} designed for {req.audience}."
        points = req.key_points or [
            "Core architecture and design trade-offs",
            "Step-by-step implementation workflow",
            "Verification, edge cases, and production deployment tips",
        ]
        code_block = (
            "\n## Implementation Blueprint\n\n"
            "```python\n"
            "# Minimal starter pattern\n"
            "def run_pipeline(config: dict) -> dict:\n"
            '    """Execute the core workflow safely with explicit validation."""\n'
            "    if not config:\n"
            '        raise ValueError("Configuration cannot be empty")\n'
            '    return {"status": "ready", "keys": sorted(config.keys())}\n'
            "```\n"
            if req.include_code_example
            else ""
        )
        sections = "\n\n".join(
            f"## {idx}. {pt}\n\n"
            f"Focus on keeping **{pt.lower()}** modular, testable, and easy to maintain for {req.audience}. "
            f"Document inputs, expected outputs, and failure modes before scaling."
            for idx, pt in enumerate(points, start=1)
        )
        markdown = (
            f"# {title}\n\n"
            f"> **Meta Description:** {meta}\n\n"
            f"## Why {req.topic.strip()} Matters\n\n"
            f"This guide breaks down **{req.topic.strip()}** in a {req.tone} style tailored for {req.audience}. "
            f"Instead of abstract theory, we focus on clean boundaries, repeatable testing, and practical execution.\n\n"
            f"{sections}\n"
            f"{code_block}\n"
            f"## Production Checklist\n\n"
            f"- Keep modules additive and isolated from core services.\n"
            f"- Add automated tests for both happy paths and failure cases.\n"
            f"- Log structured diagnostics so issues are easy to trace.\n\n"
            f"**Tags:** {', '.join('#' + t for t in tags)}\n"
        )
        return title, meta, markdown

    async def generate_video_script(self, req: VideoScriptRequest) -> VideoScriptResponse:
        system_prompt = (
            "You are a short-form technical video scriptwriter inside JARVIS OS. "
            "Write a tight, high-retention script with timestamped beats, spoken dialogue, and visual/B-roll cues."
        )
        user_prompt = (
            f"Topic: {req.topic}\n"
            f"Platform: {req.platform}\n"
            f"Duration: {req.duration_seconds} seconds\n"
            f"Audience: {req.audience}\n"
            f"Tone: {req.tone}\n"
            f"CTA: {req.call_to_action}\n"
        )

        res = await self.llm.complete(system_prompt, user_prompt)
        scenes = self._build_timed_scenes(req)
        title = f"{req.topic.strip()} ({req.duration_seconds}s {req.platform} Script)"

        if not res.used_fallback and res.text:
            full_md = res.text.strip()
        else:
            full_md = self._format_video_markdown(title, req, scenes)

        item_id = self.store.save_item(
            content_type="video_script",
            title=title,
            topic=req.topic,
            provider=res.provider_used,
            markdown=full_md,
            payload={
                "platform": req.platform,
                "duration_seconds": req.duration_seconds,
                "scenes": [model_to_dict(s) for s in scenes],
            },
        )

        return VideoScriptResponse(
            item_id=item_id,
            provider_used=res.provider_used,
            title=title,
            platform=req.platform,
            duration_seconds=req.duration_seconds,
            scenes=scenes,
            full_script_markdown=full_md,
            manual_prompt_fallback=res.manual_prompt_fallback,
        )

    @staticmethod
    def _build_timed_scenes(req: VideoScriptRequest) -> List[VideoScene]:
        d = req.duration_seconds
        t1 = max(3, int(d * 0.10))
        t2 = max(t1 + 4, int(d * 0.30))
        t3 = max(t2 + 6, int(d * 0.72))
        t4 = max(t3 + 4, int(d * 0.88))

        topic = req.topic.strip()
        return [
            VideoScene(
                timestamp=f"0:00 - 0:{t1:02d}",
                segment="Hook",
                spoken_line=f"Most people overcomplicate {topic} — here is how to build it cleanly in under a minute.",
                visual_cue=f"Fast punch-in shot showing the finished {topic} working live on screen.",
            ),
            VideoScene(
                timestamp=f"0:{t1:02d} - 0:{t2:02d}",
                segment="Problem & Setup",
                spoken_line=f"When you are building for {req.audience}, bloated dependencies and fragile glue code slow everything down.",
                visual_cue="Split-screen: messy architecture diagram vs. clean modular diagram.",
            ),
            VideoScene(
                timestamp=f"0:{t2:02d} - 0:{t3:02d}",
                segment="Core Walkthrough",
                spoken_line=f"Step one: isolate the core logic into a clean module. Step two: add a fast API layer and local persistence. Step three: verify every path with automated tests.",
                visual_cue="Screen recording zooming into 3 clean highlights (module, API response, passing tests).",
            ),
            VideoScene(
                timestamp=f"0:{t3:02d} - 0:{t4:02d}",
                segment="Proof / Payoff",
                spoken_line=f"Now {topic} runs reliably with minimal overhead and plugs straight into your main dashboard.",
                visual_cue="Live UI demo clicking through the feature with smooth status badges.",
            ),
            VideoScene(
                timestamp=f"0:{t4:02d} - 0:{d:02d}",
                segment="Call to Action",
                spoken_line=req.call_to_action,
                visual_cue="End card with concise on-screen text and arrow pointing to follow/subscribe.",
            ),
        ]

    @staticmethod
    def _format_video_markdown(title: str, req: VideoScriptRequest, scenes: List[VideoScene]) -> str:
        lines = [
            f"# {title}",
            "",
            f"- **Platform:** {req.platform}",
            f"- **Duration:** {req.duration_seconds}s",
            f"- **Tone:** {req.tone}",
            "",
            "## Shot-by-Shot Script",
            "",
        ]
        for s in scenes:
            lines.extend(
                [
                    f"### [{s.timestamp}] {s.segment}",
                    f"- **Spoken:** {s.spoken_line}",
                    f"- **Visual Cue:** {s.visual_cue}",
                    "",
                ]
            )
        return "\n".join(lines).strip() + "\n"

    async def generate_hooks_captions(self, req: HooksCaptionsRequest) -> HooksCaptionsResponse:
        system_prompt = (
            "You are a technical social content strategist inside JARVIS OS. "
            "Write punchy hooks and platform-specific captions without clickbait fluff."
        )
        user_prompt = (
            f"Topic: {req.topic}\n"
            f"Platforms: {', '.join(req.platforms)}\n"
            f"Tone: {req.tone}\n"
            f"Hook count: {req.hook_count}\n"
            f"CTA: {req.call_to_action}\n"
        )

        res = await self.llm.complete(system_prompt, user_prompt)
        hooks = self._build_hooks(req.topic, req.hook_count)
        captions = self._build_captions(req.topic, req.platforms, req.call_to_action)

        if not res.used_fallback and res.text:
            markdown = res.text.strip()
        else:
            markdown = self._format_hooks_captions_md(req.topic, hooks, captions)

        item_id = self.store.save_item(
            content_type="hooks_captions",
            title=f"Hooks & Captions: {req.topic.strip()}",
            topic=req.topic,
            provider=res.provider_used,
            markdown=markdown,
            payload={
                "hooks": [model_to_dict(h) for h in hooks],
                "captions": [model_to_dict(c) for c in captions],
            },
        )

        return HooksCaptionsResponse(
            item_id=item_id,
            provider_used=res.provider_used,
            topic=req.topic,
            hooks=hooks,
            captions=captions,
            markdown=markdown,
            manual_prompt_fallback=res.manual_prompt_fallback,
        )

    @staticmethod
    def _build_hooks(topic: str, count: int) -> List[HookItem]:
        t = topic.strip()
        catalog = [
            HookItem(style="Curiosity", text=f"I built {t} with almost zero dependencies — here is what actually worked."),
            HookItem(style="Contrarian", text=f"Stop over-engineering {t}. A clean 3-layer design beats a bloated stack every time."),
            HookItem(style="How-To", text=f"How to ship {t} in one weekend without breaking your existing project."),
            HookItem(style="Result-First", text=f"From planned roadmap card to live working feature: {t} running end-to-end."),
            HookItem(style="Mistake-Avoidance", text=f"3 silent mistakes that break {t} in production (and the exact fixes)."),
            HookItem(style="Builder Story", text=f"Day 1 of adding {t} to my personal AI system — watch how it comes together."),
            HookItem(style="Direct Value", text=f"Save this blueprint if you are building {t} this month."),
            HookItem(style="Question", text=f"What happens when you combine local persistence, clean APIs, and {t}?"),
        ]
        return catalog[:count]

    @staticmethod
    def _build_captions(topic: str, platforms: List[str], cta: str) -> List[PlatformCaption]:
        t = topic.strip()
        tags = [f"#{tag}" for tag in _extract_tags(t, ["AI", "BuildInPublic", "JARVIS"])[:5]]
        results: List[PlatformCaption] = []
        for plat in platforms:
            p_low = plat.lower()
            if "x" == p_low or "twitter" in p_low:
                text = f"Just shipped {t}: modular backend, local fallback, and automated tests. {cta} {' '.join(tags[:3])}"
            elif "linkedin" in p_low:
                text = (
                    f"We just turned {t} from a roadmap idea into a working module.\n\n"
                    f"Key design choices:\n"
                    f"• Strictly additive architecture (zero risk to existing services)\n"
                    f"• Fast local persistence & clean API boundaries\n"
                    f"• Verified with automated tests\n\n"
                    f"{cta}\n\n{' '.join(tags)}"
                )
            elif "instagram" in p_low:
                text = f"Building {t} step by step. Clean UI, fast backend, zero bloat.\n\n{cta}\n.\n.\n{' '.join(tags)}"
            else:
                text = f"Full walkthrough of {t} — architecture, live demo, and integration notes.\n\n{cta}\n\n{' '.join(tags)}"
            results.append(
                PlatformCaption(
                    platform=plat,
                    caption=text,
                    hashtags=tags,
                    character_count=len(text),
                )
            )
        return results

    @staticmethod
    def _format_hooks_captions_md(
        topic: str,
        hooks: List[HookItem],
        captions: List[PlatformCaption],
    ) -> str:
        lines = [f"# Hooks & Captions — {topic.strip()}", "", "## Scroll-Stopping Hooks", ""]
        for i, h in enumerate(hooks, start=1):
            lines.append(f"{i}. **[{h.style}]** {h.text}")
        lines.extend(["", "## Platform Captions", ""])
        for c in captions:
            lines.extend(
                [
                    f"### {c.platform} ({c.character_count} chars)",
                    "",
                    c.caption,
                    "",
                ]
            )
        return "\n".join(lines).strip() + "\n"

    async def generate_carousel(self, req: CarouselRequest) -> CarouselResponse:
        system_prompt = (
            "You are a technical visual storyteller inside JARVIS OS. "
            "Design a crisp, high-clarity slide-by-slide carousel outline with short headlines and visual cues."
        )
        user_prompt = (
            f"Topic: {req.topic}\n"
            f"Platform: {req.platform}\n"
            f"Slide count: {req.slide_count}\n"
            f"Audience: {req.audience}\n"
            f"Tone: {req.tone}\n"
        )

        res = await self.llm.complete(system_prompt, user_prompt)
        slides = self._build_carousel_slides(req)

        if not res.used_fallback and res.text:
            markdown = res.text.strip()
        else:
            markdown = self._format_carousel_md(req.topic, req.platform, slides)

        item_id = self.store.save_item(
            content_type="carousel",
            title=f"Carousel ({req.slide_count} slides): {req.topic.strip()}",
            topic=req.topic,
            provider=res.provider_used,
            markdown=markdown,
            payload={"platform": req.platform, "slides": [model_to_dict(s) for s in slides]},
        )

        return CarouselResponse(
            item_id=item_id,
            provider_used=res.provider_used,
            topic=req.topic,
            platform=req.platform,
            slides=slides,
            markdown=markdown,
            manual_prompt_fallback=res.manual_prompt_fallback,
        )

    @staticmethod
    def _build_carousel_slides(req: CarouselRequest) -> List[CarouselSlide]:
        t = req.topic.strip()
        total = req.slide_count
        slides: List[CarouselSlide] = [
            CarouselSlide(
                slide_number=1,
                role="Cover Hook",
                headline=f"{t}: The Clean Architecture Playbook",
                body=f"A {total}-slide breakdown for {req.audience}. Swipe to see how every piece connects.",
                visual_note="Bold high-contrast cover with clean system icon and swipe indicator.",
            ),
            CarouselSlide(
                slide_number=2,
                role="Problem",
                headline="Why Most Setups Break Early",
                body="Tightly coupled scripts, missing fallbacks, and untested changes turn small features into debugging nightmares.",
                visual_note="Two-column contrast card: fragile monolith vs. modular plugin.",
            ),
        ]

        middle_steps = [
            ("Step 1: Define Clean Schemas", "Lock down typed inputs and outputs first so UI and backend never drift.", "Schema box diagram"),
            ("Step 2: Isolate Core Logic", "Keep business logic independent of HTTP routes so it is effortless to test.", "Layered module stack"),
            ("Step 3: Add Resilient Fallbacks", "Support cloud models when online and deterministic local logic when offline.", "Provider failover flow"),
            ("Step 4: Persist State Locally", "Use lightweight SQLite WAL storage for instant history without heavy DB servers.", "SQLite table badge"),
            ("Step 5: Automate Verification", "Run fast unit and API tests before integrating into your live system.", "Green test-pass terminal card"),
            ("Step 6: Ship Additively", "Mount via a router so existing features stay untouched and safe.", "Router plug-in graphic"),
            ("Step 7: Measure & Iterate", "Track usage history and refine prompts or workflows based on real runs.", "Metrics & feedback loop"),
            ("Step 8: Export & Repurpose", "Turn every run into reusable Markdown or JSON assets.", "Export format icons"),
        ]

        middle_needed = max(1, total - 3)
        for idx in range(middle_needed):
            title, body, visual = middle_steps[idx % len(middle_steps)]
            slides.append(
                CarouselSlide(
                    slide_number=len(slides) + 1,
                    role=f"Step {idx + 1}",
                    headline=title,
                    body=body,
                    visual_note=visual,
                )
            )

        slides.append(
            CarouselSlide(
                slide_number=len(slides) + 1,
                role="Closing CTA",
                headline=f"Ready to Build {t}?",
                body="Bookmark this carousel, share it with a fellow builder, and drop your next feature request in the comments.",
                visual_note="Clean summary checklist + bookmark & follow callout.",
            )
        )
        return slides

    @staticmethod
    def _format_carousel_md(topic: str, platform: str, slides: List[CarouselSlide]) -> str:
        lines = [f"# Carousel Outline — {topic.strip()} ({platform})", ""]
        for s in slides:
            lines.extend(
                [
                    f"## Slide {s.slide_number}: {s.headline} ({s.role})",
                    f"- **Copy:** {s.body}",
                    f"- **Visual Note:** {s.visual_note}",
                    "",
                ]
            )
        return "\n".join(lines).strip() + "\n"

    async def generate_campaign(self, req: CampaignRequest) -> CampaignResponse:
        blog = await self.generate_blog(
            BlogRequest(topic=req.topic, audience=req.audience, tone=req.tone)
        )
        video = await self.generate_video_script(
            VideoScriptRequest(
                topic=req.topic,
                duration_seconds=req.video_duration_seconds,
                audience=req.audience,
                tone=req.tone,
                call_to_action=req.call_to_action,
            )
        )
        hooks = await self.generate_hooks_captions(
            HooksCaptionsRequest(
                topic=req.topic,
                tone=req.tone,
                call_to_action=req.call_to_action,
            )
        )
        carousel = await self.generate_carousel(
            CarouselRequest(
                topic=req.topic,
                slide_count=req.carousel_slides,
                audience=req.audience,
                tone=req.tone,
            )
        )

        combined = (
            f"# Full Content Campaign: {req.topic.strip()}\n\n"
            f"{blog.markdown}\n\n"
            f"{video.full_script_markdown}\n\n"
            f"{hooks.markdown}\n\n"
            f"{carousel.markdown}\n"
        )

        campaign_id = self.store.save_item(
            content_type="campaign",
            title=f"Full Campaign: {req.topic.strip()}",
            topic=req.topic,
            provider=blog.provider_used,
            markdown=combined,
            payload={
                "blog_id": blog.item_id,
                "video_script_id": video.item_id,
                "hooks_captions_id": hooks.item_id,
                "carousel_id": carousel.item_id,
            },
        )

        return CampaignResponse(
            campaign_id=campaign_id,
            topic=req.topic,
            blog=blog,
            video_script=video,
            hooks_captions=hooks,
            carousel=carousel,
            combined_markdown=combined,
        )
