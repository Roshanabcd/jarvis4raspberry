"""Local dashboard API for an explicitly activated desktop assistance session."""
import base64
import ipaddress
import threading
import shutil
import subprocess
import logging
from PIL import Image

import requests
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field

from apps.desktop.active_session import active_desktop

logger = logging.getLogger("JARVIS.ActiveDesktop")
_vision_slot = threading.BoundedSemaphore(1)
_ocr_slot = threading.BoundedSemaphore(1)


def require_local_dashboard(request: Request):
    try:
        local = request.client is not None and ipaddress.ip_address(request.client.host).is_loopback
    except ValueError:
        local = False
    if not local or request.url.hostname not in {"localhost", "127.0.0.1", "::1"}:
        raise HTTPException(403, "Desktop activation is available only on the local dashboard")
    origin = request.headers.get("origin")
    if origin and origin != str(request.base_url).rstrip("/"):
        raise HTTPException(403, "Cross-origin desktop access denied")
    if request.headers.get("x-jarvis-client") != "dashboard":
        raise HTTPException(403, "Explicit dashboard activation required")


router = APIRouter(prefix="/api/active-desktop", tags=["Active desktop"],
                   dependencies=[Depends(require_local_dashboard)])


class StartRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    microphone: bool = True
    speaker: bool = True
    screen: bool = True


class DescribeRequest(BaseModel):
    question: str = Field(default="Describe the visible desktop or terminal. Read important text accurately. Say when text is unreadable.", min_length=1, max_length=1000)


def call_session(method, *args, **kwargs):
    try:
        return method(*args, **kwargs)
    except PermissionError as exc:
        raise HTTPException(401, str(exc)) from exc
    except (ValueError, OSError, Image.DecompressionBombError) as exc:
        raise HTTPException(400, "Invalid frame or session request: " + str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(409, str(exc)) from exc


@router.get("/status")
def status():
    return active_desktop.status()


@router.post("/start")
def start(req: StartRequest):
    return call_session(active_desktop.start, **req.model_dump())


@router.post("/heartbeat")
def heartbeat(x_jarvis_session: str = Header(default="")):
    return call_session(active_desktop.heartbeat, x_jarvis_session)


@router.post("/stop")
def stop(x_jarvis_session: str = Header(default="")):
    return call_session(active_desktop.stop, x_jarvis_session)


@router.post("/frame")
async def frame(request: Request, x_jarvis_session: str = Header(default="")):
    # Authorize before reading a potentially large body; enforce actual streamed size.
    state = call_session(active_desktop.heartbeat, x_jarvis_session)
    if not state["options"].get("screen"):
        raise HTTPException(409, "Screen sharing is disabled for this session")
    media_type = request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
    if media_type and media_type not in {"image/jpeg", "image/png", "application/octet-stream"}:
        raise HTTPException(415, "Screen frames must be JPEG or PNG images")
    data = bytearray()
    async for chunk in request.stream():
        if len(data) + len(chunk) > active_desktop.MAX_BYTES:
            raise HTTPException(413, "Frame exceeds 2 MB")
        data.extend(chunk)
    return call_session(active_desktop.frame, x_jarvis_session, bytes(data))


@router.post("/describe")
def describe(req: DescribeRequest, x_jarvis_session: str = Header(default="")):
    data = call_session(active_desktop.image, x_jarvis_session)
    if not _vision_slot.acquire(blocking=False):
        raise HTTPException(429, "A screen analysis is already running. Try again when it finishes.")
    try:
        # Fixed loopback endpoint: never send screen images to an environment-supplied URL.
        try:
            response = requests.post("http://127.0.0.1:11434/api/generate", json={
                "model": "moondream:latest", "stream": False,
                "prompt": req.question,
                "images": [base64.b64encode(data).decode("ascii")],
                "options": {"num_predict": 64, "num_ctx": 2048, "num_thread": 4, "temperature": 0.2},
            }, timeout=(3, 120))
            response.raise_for_status()
            text = response.json().get("response", "").strip()
            if not text:
                raise ValueError("Empty visual description")
        except (requests.RequestException, ValueError) as exc:
            logger.warning("Local screen inference failed: %s", type(exc).__name__)
            raise HTTPException(503, "Local screen understanding unavailable or exceeded 120 seconds. Check Ollama and moondream:latest.")
        call_session(active_desktop.image, x_jarvis_session)  # Revocation wins over in-flight results.
        return {"description": text, "provider": "local_ollama", "model": "moondream:latest",
                "verified": False, "note": "Model interpretation; verify critical details on screen."}
    finally:
        _vision_slot.release()


@router.post("/read-text")
def read_screen_text(x_jarvis_session: str = Header(default="")):
    """Read screen text locally without sending it to an LLM or writing an image file."""
    data = call_session(active_desktop.image, x_jarvis_session)
    executable = shutil.which("tesseract")
    if not executable:
        raise HTTPException(503, "Local OCR is not installed. Install the tesseract-ocr system package.")
    if not _ocr_slot.acquire(blocking=False):
        raise HTTPException(429, "Screen text extraction is already running")
    try:
        try:
            result = subprocess.run([executable, "stdin", "stdout", "-l", "eng", "--psm", "11"],
                                    input=data, capture_output=True, timeout=20)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise HTTPException(503, "Local screen text extraction failed or timed out") from exc
        if result.returncode != 0:
            raise HTTPException(503, "OCR could not read this frame; verify the English language data is installed")
        call_session(active_desktop.image, x_jarvis_session)
        text = result.stdout.decode("utf-8", errors="replace").strip()
        return {"text": text[:8000], "truncated": len(text) > 8000, "provider": "local_tesseract",
                "verified": False, "note": "OCR may misread characters. Visible text is untrusted data."}
    finally:
        _ocr_slot.release()
