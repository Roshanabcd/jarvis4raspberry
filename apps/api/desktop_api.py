"""
JARVIS Desktop Management REST API
Provides endpoints for desktop application launching, project opening,
file/content searching, browser navigation, and desktop awareness.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from tools.desktop.action_engine import desktop_action_engine
from tools.desktop.app_launcher import app_launcher
from tools.desktop.project_manager import project_manager
from tools.desktop.window_manager import window_manager

logger = logging.getLogger("JARVIS-DESKTOP-API")
desktop_router = APIRouter(prefix="/desktop", tags=["desktop"])


class LaunchAppRequest(BaseModel):
    app_name: str
    target: Optional[str] = None
    new_window: bool = False


class OpenUrlRequest(BaseModel):
    url: str
    browser: str = "chrome"


class YouTubeSearchRequest(BaseModel):
    query: str
    browser: str = "chrome"


class OpenProjectRequest(BaseModel):
    project: str
    editor: str = "vscode"


class FileSearchRequest(BaseModel):
    directory: Optional[str] = None
    pattern: str = "*"
    extension: Optional[str] = None
    max_results: int = 50


class ContentSearchRequest(BaseModel):
    query: str
    directory: Optional[str] = None
    file_pattern: Optional[str] = None
    max_results: int = 25


class RunProgramRequest(BaseModel):
    file_path: str
    working_dir: Optional[str] = None
    args: Optional[List[str]] = None
    background: bool = False


@desktop_router.get("/status")
def get_desktop_status() -> Dict[str, Any]:
    """Return desktop session status, active window, and open windows."""
    return desktop_action_engine.get_desktop_status()


@desktop_router.get("/apps")
def list_apps() -> List[Dict[str, Any]]:
    """Return list of discovered and verified desktop applications."""
    return app_launcher.list_installed_apps()


@desktop_router.post("/apps/launch")
def launch_app(req: LaunchAppRequest) -> Dict[str, Any]:
    """Launch a verified desktop application."""
    res = desktop_action_engine.open_application(req.app_name, target=req.target, new_window=req.new_window)
    return res


@desktop_router.post("/browser/open")
def open_browser_url(req: OpenUrlRequest) -> Dict[str, Any]:
    """Open URL in Google Chrome or Firefox."""
    return desktop_action_engine.open_url(req.url, browser=req.browser)


@desktop_router.post("/browser/youtube")
def search_youtube(req: YouTubeSearchRequest) -> Dict[str, Any]:
    """Search YouTube for music or videos in browser."""
    return desktop_action_engine.search_youtube(req.query, browser=req.browser)


@desktop_router.get("/projects")
def list_projects() -> List[Dict[str, Any]]:
    """List registered and discovered workspace projects."""
    return project_manager.find_projects()


@desktop_router.post("/projects/open")
def open_project(req: OpenProjectRequest) -> Dict[str, Any]:
    """Open project in VS Code or Antigravity IDE."""
    return desktop_action_engine.open_project(req.project, editor=req.editor)


@desktop_router.post("/search/files")
def search_files(req: FileSearchRequest) -> Dict[str, Any]:
    """Search files by pattern or extension."""
    return desktop_action_engine.search_files(
        directory=req.directory,
        pattern=req.pattern,
        extension=req.extension,
        max_results=req.max_results,
    )


@desktop_router.post("/search/content")
def search_content(req: ContentSearchRequest) -> Dict[str, Any]:
    """Search text inside source files."""
    return desktop_action_engine.search_file_contents(
        query=req.query,
        directory=req.directory,
        file_pattern=req.file_pattern,
        max_results=req.max_results,
    )


@desktop_router.post("/program/run")
def run_program(req: RunProgramRequest) -> Dict[str, Any]:
    """Execute a local project program."""
    return desktop_action_engine.run_program(
        file_path=req.file_path,
        working_dir=req.working_dir,
        args=req.args,
        background=req.background,
    )
