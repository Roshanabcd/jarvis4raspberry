"""Voice REST API for JARVIS OS — speech control, status, devices, and push-to-talk."""
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from apps.voice.service import voice_service

logger = logging.getLogger("JARVIS.API.Voice")
voice_router = APIRouter(prefix="/voice", tags=["voice"])


class CommandRequest(BaseModel):
    text: str


class ListenOnceRequest(BaseModel):
    duration_secs: Optional[int] = 4


class SynthesizeRequest(BaseModel):
    text: str
    voice_type: Optional[str] = "cloned"


@voice_router.get("/status")
def get_voice_status():
    """Return real-time voice pipeline state and hardware device status."""
    return voice_service.get_state()


@voice_router.post("/start")
def start_voice_listening():
    """Start continuous background wake-word listening loop."""
    voice_service.start()
    return {"status": "ok", "state": voice_service.get_state()}


@voice_router.post("/stop")
def stop_voice_listening():
    """Stop continuous background listening loop."""
    voice_service.stop()
    return {"status": "ok", "state": voice_service.get_state()}


@voice_router.post("/mute")
def mute_voice():
    """Mute microphone capture."""
    voice_service.mute()
    return {"status": "ok", "muted": True, "state": voice_service.get_state()}


@voice_router.post("/unmute")
def unmute_voice():
    """Unmute microphone capture."""
    voice_service.unmute()
    return {"status": "ok", "muted": False, "state": voice_service.get_state()}


@voice_router.post("/interrupt")
def interrupt_speech():
    """Immediately halt any active voice playback (barge-in)."""
    voice_service.stop_playback()
    return {"status": "ok", "interrupted": True}


@voice_router.post("/listen_once")
def listen_once(req: ListenOnceRequest = ListenOnceRequest()):
    """Push-to-talk: capture audio for N seconds from ReSpeaker Lite, transcribe and process."""
    result = voice_service.listen_once(duration_secs=req.duration_secs or 4)
    return result


@voice_router.get("/devices")
def list_audio_devices():
    """Return all detected audio input (microphones) and output (speakers) devices."""
    mgr = voice_service.audio_manager
    inputs = mgr.detect_devices()
    outputs = mgr.detect_playback_devices()
    best_in = mgr.select_best_device()
    best_out = mgr.select_best_playback_device()
    return {
        "input_devices": inputs,
        "output_devices": outputs,
        "selected_input": best_in,
        "selected_output": best_out,
        "microphone_available": mgr.is_microphone_available(),
    }


@voice_router.post("/command")
def run_command(req: CommandRequest):
    """Execute text command through voice pipeline dialogue manager."""
    response = voice_service.process_command(req.text)
    return {"status": "ok", "response": response}


@voice_router.post("/synthesize")
def synthesize_speech(req: SynthesizeRequest):
    """Synthesize text using OmniVoice custom cloned voice or fast offline fallback."""
    from apps.voice.gradio_tts import gradio_cloner
    res = gradio_cloner.synthesize(req.text)
    return {
        "status": "ok",
        "audio_path": res.audio_path,
        "cached": res.cached,
        "provider": res.provider,
        "latency_ms": res.latency_ms,
        "error": res.error,
    }
