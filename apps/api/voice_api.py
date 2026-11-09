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
    speed: Optional[float] = None
    num_steps: Optional[int] = None
    reference_text: Optional[str] = None


class VoiceTuningRequest(BaseModel):
    speed: Optional[float] = None
    num_steps: Optional[int] = None
    reference_text: Optional[str] = None
    reference_audio_path: Optional[str] = None


@voice_router.get("/status")
def get_voice_status():
    """Return real-time voice pipeline state and hardware device status."""
    from apps.voice.speech_manager import speech_manager
    st = voice_service.get_state()
    diag = speech_manager.get_status()
    st["diagnostics"] = diag
    st["speaker"] = diag["speaker"]
    st["tts"] = diag["tts"]
    return st


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
@voice_router.post("/speak")
def synthesize_speech(req: SynthesizeRequest):
    """Synthesize text using OmniVoice custom cloned voice or fast offline fallback, staging audio."""
    from apps.voice.speech_manager import speech_manager
    v_cfg = {}
    if req.speed is not None:
        v_cfg["speed"] = req.speed
    if req.num_steps is not None:
        v_cfg["num_steps"] = req.num_steps
    if req.reference_text is not None:
        v_cfg["reference_text"] = req.reference_text
    res = speech_manager.synthesize_and_stage(req.text, play_system=True, voice_config=v_cfg or None)
    return res


@voice_router.post("/tuning")
def update_voice_tuning(req: VoiceTuningRequest):
    """Update voice speed, diffusion steps, reference text, or reference audio."""
    from apps.voice.gradio_tts import gradio_cloner
    updates = {}
    if req.speed is not None and 0.5 <= req.speed <= 2.0:
        gradio_cloner.default_speed = float(req.speed)
        updates["speed"] = gradio_cloner.default_speed
    if req.num_steps is not None and 8 <= req.num_steps <= 64:
        gradio_cloner.default_num_steps = int(req.num_steps)
        updates["num_steps"] = gradio_cloner.default_num_steps
    if req.reference_text is not None and req.reference_text.strip():
        gradio_cloner.reference_text = req.reference_text.strip()
        updates["reference_text"] = gradio_cloner.reference_text
    if req.reference_audio_path is not None and os.path.exists(req.reference_audio_path):
        gradio_cloner.reference_voice_path = req.reference_audio_path
        updates["reference_audio_path"] = gradio_cloner.reference_voice_path

    return {
        "status": "ok",
        "applied": updates,
        "current": {
            "speed": gradio_cloner.default_speed,
            "num_steps": gradio_cloner.default_num_steps,
            "reference_text": gradio_cloner.reference_text,
            "reference_audio_path": gradio_cloner.reference_voice_path,
        }
    }


@voice_router.get("/tuning")
def get_voice_tuning():
    """Get current voice generation tuning parameters."""
    from apps.voice.gradio_tts import gradio_cloner
    return {
        "status": "ok",
        "speed": gradio_cloner.default_speed,
        "num_steps": gradio_cloner.default_num_steps,
        "reference_text": gradio_cloner.reference_text,
        "reference_audio_path": gradio_cloner.reference_voice_path,
    }


@voice_router.get("/audio/{audio_id}")
def get_staged_audio_file(audio_id: str):
    """Serve staged audio file for browser HTML5 audio element."""
    from fastapi.responses import FileResponse
    from apps.voice.speech_manager import speech_manager
    audio = speech_manager.get_staged_audio(audio_id)
    if not audio:
        raise HTTPException(status_code=404, detail="Audio file not found or expired")
    file_path, media_type = audio
    return FileResponse(file_path, media_type=media_type, headers={"Accept-Ranges": "bytes"})


@voice_router.post("/test/microphone")
def test_microphone_endpoint(duration_secs: int = 3):
    """Record real audio from ReSpeaker microphone and transcribe without simulation."""
    from apps.voice.speech_manager import speech_manager
    return speech_manager.test_microphone(duration_secs=duration_secs)


@voice_router.post("/test/speaker")
def test_speaker_endpoint():
    """Test physical speaker output."""
    from apps.voice.speech_manager import speech_manager
    return speech_manager.test_speaker()


@voice_router.get("/diagnostics")
def get_voice_diagnostics():
    """Return comprehensive diagnostics for audio hardware, cloner, and playback."""
    from apps.voice.speech_manager import speech_manager
    return speech_manager.get_status()


@voice_router.post("/replay/{audio_id}")
def replay_audio_endpoint(audio_id: str):
    """Replay a staged audio file through system speaker."""
    from apps.voice.speech_manager import speech_manager
    audio = speech_manager.get_staged_audio(audio_id)
    if not audio:
        raise HTTPException(status_code=404, detail="Audio file not found")
    path, _ = audio
    ok = speech_manager.play_system_audio(path)
    return {"status": "ok" if ok else "error", "audio_id": audio_id, "replayed": ok}


@voice_router.get("/cache/stats")
def voice_cache_stats():
    from apps.voice.gradio_tts import gradio_cloner
    entries = gradio_cloner._count_cache_entries()
    return {"status": "ok", "cached_files": entries}


@voice_router.post("/cache/clear")
def clear_voice_cache():
    import glob
    import os
    from apps.voice.gradio_tts import gradio_cloner
    purged = 0
    if os.path.isdir(gradio_cloner.cache_dir):
        for f in glob.glob(os.path.join(gradio_cloner.cache_dir, "*")):
            try:
                os.remove(f)
                purged += 1
            except Exception:
                pass
    return {"status": "ok", "purged": purged}


# ─── Google Colab OmniVoice Integration Aliases ──────────────
from fastapi import Request
from apps.voice.colab_registration import colab_manager


class ColabVoiceRegisterRequest(BaseModel):
    gradio_url: str
    session_id: Optional[str] = None
    token: Optional[str] = None
    verify: Optional[bool] = True


@voice_router.post("/colab/register")
def register_colab_url_alias(req: ColabVoiceRegisterRequest, request: Request):
    """Alias for POST /api/integrations/omnivoice/register."""
    client_ip = request.client.host if request.client else "unknown"
    is_local = client_ip in ("127.0.0.1", "localhost", "::1", "testclient")
    result = colab_manager.register_url(
        gradio_url=req.gradio_url,
        session_id=req.session_id,
        token=req.token,
        is_local_request=is_local,
        client_ip=client_ip,
        verify_now=bool(req.verify),
    )
    if result.get("status") == "error":
        raise HTTPException(status_code=result.get("code", 400), detail=result.get("message", "Registration failed"))
    return result


@voice_router.get("/colab/status")
def get_colab_status_alias():
    """Alias for GET /api/integrations/omnivoice/status."""
    return colab_manager.get_status()


@voice_router.post("/colab/verify")
def verify_colab_url_alias(gradio_url: Optional[str] = None):
    """Alias for POST /api/integrations/omnivoice/verify."""
    url = (gradio_url or "").strip() or colab_manager.get_active_url()
    if not url:
        raise HTTPException(status_code=400, detail="No Gradio URL specified or active")
    ok, msg, endpoints = colab_manager.verify_remote_gradio(url)
    return {"status": "ok" if ok else "error", "gradio_url": url, "verified": ok, "message": msg, "endpoints": endpoints}


@voice_router.get("/colab/runner")
def get_colab_runner_status():
    """Retrieve status, live logs, and active URL of the automated Colab OmniVoice runner."""
    from apps.voice.colab_runner import colab_runner
    return colab_runner.status()


@voice_router.post("/colab/runner/start")
def start_colab_runner():
    """Trigger background execution of Super_Eleven_Lab_Lite_2_1.ipynb on Google Colab."""
    from apps.voice.colab_runner import colab_runner
    ok = colab_runner.start(restart_if_running=True)
    return {"status": "ok" if ok else "error", "running": colab_runner.is_running(), "state": colab_runner.state}


@voice_router.post("/colab/runner/stop")
def stop_colab_runner():
    """Stop the Colab runner background process."""
    from apps.voice.colab_runner import colab_runner
    return colab_runner.stop()


@voice_router.post("/colab/test")
def test_colab_voice_alias():
    """Alias for POST /api/integrations/omnivoice/test."""
    from apps.voice.speech_manager import speech_manager
    res = speech_manager.synthesize_and_stage(
        "Google Colab OmniVoice connection verified. My personal voice model is active.",
        play_system=True
    )
    return {
        "status": "ok" if res.get("success") else "error",
        "synthesis": res,
        "is_cloned": res.get("is_cloned", False),
        "provider": res.get("provider", "unknown"),
        "audio_url": res.get("audio_url"),
    }

