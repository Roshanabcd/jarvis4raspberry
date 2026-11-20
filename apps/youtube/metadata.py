"""
YouTube Video Metadata Service.
Integrates official YouTube Data API v3 when an API key is configured.
Supports public oEmbed fallback without inventing metadata.
"""
import logging
import os
import re
from typing import Any, Dict, Optional
import requests

from config.config_manager import config
from .models import YouTubeVideoInfo

logger = logging.getLogger("JARVIS.YouTube.Metadata")

_ISO_DURATION_RE = re.compile(
    r"^P(?:(?P<days>\d+)D)?(?:T(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?(?:(?P<seconds>\d+)S)?)?$"
)


def parse_iso8601_duration(duration_str: str) -> int:
    """Parse ISO 8601 duration string (e.g. PT15M33S, PT1H2M10S) into total seconds."""
    if not duration_str or not isinstance(duration_str, str):
        return 0
    m = _ISO_DURATION_RE.match(duration_str.strip())
    if not m:
        return 0
    days = int(m.group("days") or 0)
    hours = int(m.group("hours") or 0)
    minutes = int(m.group("minutes") or 0)
    seconds = int(m.group("seconds") or 0)
    return days * 86400 + hours * 3600 + minutes * 60 + seconds


def format_seconds_duration(total_seconds: int) -> str:
    """Format total seconds into HH:MM:SS or MM:SS."""
    h, rem = divmod(total_seconds, 3600)
    m, s = divmod(rem, 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


class YouTubeMetadataService:
    def __init__(self, api_key: Optional[str] = None):
        self._api_key = api_key or os.environ.get("YOUTUBE_API_KEY") or os.environ.get("GOOGLE_API_KEY") or config.get("youtube_api_key")
        self.last_quota_error: Optional[str] = None

    def get_api_key(self) -> Optional[str]:
        return self._api_key or os.environ.get("YOUTUBE_API_KEY") or os.environ.get("GOOGLE_API_KEY") or config.get("youtube_api_key")

    def set_api_key(self, api_key: str):
        self._api_key = api_key.strip()

    def is_api_configured(self) -> bool:
        key = self.get_api_key()
        return bool(key and key.strip() and not key.startswith("your_"))

    def fetch_metadata(self, video_id: str) -> YouTubeVideoInfo:
        """
        Fetch video metadata from YouTube Data API v3 if configured,
        or fallback to public oEmbed API.
        """
        url = f"https://www.youtube.com/watch?v={video_id}"
        api_key = self.get_api_key()

        if self.is_api_configured():
            try:
                # Official YouTube Data API v3 videos.list
                endpoint = "https://www.googleapis.com/youtube/v3/videos"
                params = {
                    "part": "snippet,contentDetails,status",
                    "id": video_id,
                    "key": api_key,
                }
                r = requests.get(endpoint, params=params, timeout=5.0)
                if r.status_code == 200:
                    data = r.json()
                    items = data.get("items", [])
                    if items:
                        item = items[0]
                        snippet = item.get("snippet", {})
                        content = item.get("contentDetails", {})
                        status = item.get("status", {})

                        dur_sec = parse_iso8601_duration(content.get("duration", ""))
                        captions_available = content.get("caption") == "true"
                        embeddable = status.get("embeddable", True)

                        thumb = ""
                        thumbnails = snippet.get("thumbnails", {})
                        for size in ("maxres", "standard", "high", "medium", "default"):
                            if size in thumbnails and "url" in thumbnails[size]:
                                thumb = thumbnails[size]["url"]
                                break

                        return YouTubeVideoInfo(
                            video_id=video_id,
                            url=url,
                            title=snippet.get("title", f"YouTube Video ({video_id})"),
                            channel_title=snippet.get("channelTitle", "Unknown Channel"),
                            channel_id=snippet.get("channelId"),
                            duration_seconds=dur_sec,
                            duration_formatted=format_seconds_duration(dur_sec),
                            thumbnail_url=thumb or f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg",
                            published_at=snippet.get("publishedAt"),
                            description=snippet.get("description", ""),
                            captions_available=captions_available,
                            metadata_source="youtube_data_api_v3",
                            embed_permitted=embeddable,
                        )
                elif r.status_code == 403:
                    self.last_quota_error = "YouTube Data API quota exceeded or key unauthorized"
                    logger.warning("YouTube Data API 403: %s", r.text[:200])
            except Exception as e:
                logger.warning("YouTube Data API call error: %s", e)

        # Fallback to public oEmbed (does not require API key)
        try:
            oembed_url = f"https://www.youtube.com/oembed?url={url}&format=json"
            r = requests.get(oembed_url, timeout=4.0)
            if r.status_code == 200:
                data = r.json()
                return YouTubeVideoInfo(
                    video_id=video_id,
                    url=url,
                    title=data.get("title", f"YouTube Video ({video_id})"),
                    channel_title=data.get("author_name", "Unknown Channel"),
                    channel_id=None,
                    duration_seconds=0,
                    duration_formatted="Unknown",
                    thumbnail_url=data.get("thumbnail_url", f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"),
                    published_at=None,
                    description="",
                    captions_available=False,
                    metadata_source="public_oembed",
                    embed_permitted=True,
                )
        except Exception as oe_err:
            logger.debug("YouTube oEmbed call error: %s", oe_err)

        # Default minimal metadata without fabrication
        return YouTubeVideoInfo(
            video_id=video_id,
            url=url,
            title=f"YouTube Video ({video_id})",
            channel_title="YouTube Channel",
            thumbnail_url=f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg",
            metadata_source="unconfigured_api_key",
            embed_permitted=True,
        )


metadata_service = YouTubeMetadataService()
