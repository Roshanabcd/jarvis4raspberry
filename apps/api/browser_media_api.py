"""
Browser, Media, Audio Stream, and Theme REST API for JARVIS OS.
Provides programmatic control over browser tabs, organic search sessions,
YouTube playback and player state, PipeWire per-stream volume, audio ducking,
and live CSS theme customization.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from tools.browser.browser_agent import browser_agent
from tools.browser.search_manager import search_manager
from tools.browser.youtube_controller import youtube_controller
from tools.media.audio_stream_manager import audio_stream_manager
from tools.desktop.theme_manager import theme_manager
from apps.voice.wake_word_engine import wake_word_engine

logger = logging.getLogger("JARVIS-BROWSER-MEDIA-API")

browser_media_router = APIRouter()


# ─── Pydantic Request Models ──────────────────────────────────
class SearchRequest(BaseModel):
    query: str
    max_results: Optional[int] = 10


class OpenResultRequest(BaseModel):
    index: int
    new_tab: Optional[bool] = False
    browser: Optional[str] = "chrome"


class NavigateRequest(BaseModel):
    action: str  # back, forward, reload, close_tab, scroll_down, scroll_up
    browser: Optional[str] = "chrome"


class YouTubePlayRequest(BaseModel):
    index: Optional[int] = None
    query: Optional[str] = None
    browser: Optional[str] = "chrome"


class YouTubeControlRequest(BaseModel):
    action: str  # pause, resume, fullscreen, mute, volume
    value: Optional[int] = None


class StreamVolumeRequest(BaseModel):
    app: Optional[str] = None
    stream_id: Optional[int] = None
    volume_pct: Optional[int] = None
    volume_fraction: Optional[float] = None


class MasterVolumeRequest(BaseModel):
    volume_pct: int


class ThemeUpdateRequest(BaseModel):
    command: Optional[str] = None
    variables: Optional[Dict[str, str]] = None


# ─── Browser & Web Search Endpoints ───────────────────────────
@browser_media_router.get("/browser/search")
def search_get(q: str = Query(..., description="Search query string"), max_results: int = 10):
    return search_manager.search_web(q, max_results=max_results)


@browser_media_router.post("/browser/search")
def search_post(req: SearchRequest):
    return search_manager.search_web(req.query, max_results=req.max_results or 10)


@browser_media_router.get("/browser/session")
def get_browser_session():
    return search_manager.get_active_session() or {"status": "none", "message": "No active search session."}


@browser_media_router.post("/browser/open-result")
def open_result(req: OpenResultRequest):
    res = search_manager.open_result_by_index(req.index, new_tab=req.new_tab or False, browser=req.browser or "chrome")
    if res.get("status") == "error":
        raise HTTPException(status_code=400, detail=res.get("message"))
    return res


@browser_media_router.post("/browser/navigate")
def browser_navigate(req: NavigateRequest):
    act = req.action.lower()
    b = req.browser or "chrome"
    if act == "back":
        return browser_agent.go_back(b)
    elif act == "forward":
        return browser_agent.go_forward(b)
    elif act == "reload":
        return browser_agent.reload(b)
    elif act == "close_tab":
        return browser_agent.close_tab(b)
    elif "scroll" in act:
        direction = "down" if "down" in act else "up"
        return browser_agent.scroll(direction, b)
    raise HTTPException(status_code=400, detail=f"Unknown browser action '{req.action}'")


# ─── YouTube Controller Endpoints ─────────────────────────────
@browser_media_router.get("/browser/youtube/search")
def youtube_search_get(q: str = Query(..., description="YouTube query string"), max_results: int = 5):
    return youtube_controller.search(q, max_results=max_results)


@browser_media_router.post("/browser/youtube/search")
def youtube_search_post(req: SearchRequest):
    return youtube_controller.search(req.query, max_results=req.max_results or 5)


@browser_media_router.get("/browser/youtube/status")
def youtube_status():
    return youtube_controller.get_player_state()


@browser_media_router.post("/browser/youtube/play")
def youtube_play(req: YouTubePlayRequest):
    if req.index is not None:
        res = youtube_controller.play_video_by_index(req.index, browser=req.browser or "chrome")
    elif req.query:
        res = youtube_controller.play_direct_query(req.query, browser=req.browser or "chrome")
    else:
        raise HTTPException(status_code=400, detail="Must provide either index or query.")
    if res.get("status") == "error":
        raise HTTPException(status_code=400, detail=res.get("message"))
    return res


@browser_media_router.post("/browser/youtube/control")
def youtube_control(req: YouTubeControlRequest):
    act = req.action.lower()
    if act == "pause":
        return youtube_controller.pause()
    elif act in ("resume", "play"):
        return youtube_controller.resume()
    elif act in ("fullscreen", "full"):
        return youtube_controller.toggle_fullscreen()
    elif act == "mute":
        return youtube_controller.mute()
    elif act == "volume":
        vol = req.value if req.value is not None else 50
        return youtube_controller.set_video_volume(vol)
    raise HTTPException(status_code=400, detail=f"Unknown YouTube control action '{req.action}'")


# ─── Audio Stream Management Endpoints ────────────────────────
@browser_media_router.get("/media/streams")
def list_audio_streams():
    streams = audio_stream_manager.list_active_streams()
    master = audio_stream_manager.get_master_sink_volume()
    return {"streams": streams, "master_sink": master}


@browser_media_router.post("/media/stream/volume")
def set_stream_volume(req: StreamVolumeRequest):
    if req.app and req.volume_pct is not None:
        return audio_stream_manager.set_app_volume(req.app, req.volume_pct)
    elif req.stream_id is not None and req.volume_fraction is not None:
        ok = audio_stream_manager.set_stream_volume(req.stream_id, req.volume_fraction)
        return {"stream_id": req.stream_id, "volume_fraction": req.volume_fraction, "success": ok}
    raise HTTPException(status_code=400, detail="Provide (app, volume_pct) or (stream_id, volume_fraction).")


@browser_media_router.post("/media/master/volume")
def set_master_volume(req: MasterVolumeRequest):
    return audio_stream_manager.set_master_sink_volume(req.volume_pct)


# ─── Voice Wake State Endpoints ───────────────────────────────
@browser_media_router.get("/voice/wake-state")
def get_wake_state():
    return wake_word_engine.get_status()


# ─── Theme Customization Endpoints ────────────────────────────
@browser_media_router.get("/theme")
def get_current_theme():
    return theme_manager.get_theme()


@browser_media_router.post("/theme")
def update_theme(req: ThemeUpdateRequest):
    if req.command:
        return theme_manager.process_natural_language(req.command)
    elif req.variables:
        return theme_manager.set_theme_vars(req.variables)
    raise HTTPException(status_code=400, detail="Must provide either natural language command or variables dict.")


@browser_media_router.post("/theme/reset")
def reset_theme():
    return theme_manager.reset_theme()
