"""Voice REST API for JARVIS OS — speech control, status, devices, and push-to-talk."""
import os
import logging
from typing import Optional
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from apps.voice.service import voice_service
from apps.voice.remote_control_policy import require_external_voice_control

logger = logging.getLogger("JARVIS.API.Voice")
voice_router = APIRouter(prefix="/voice", tags=["voice"])


def _send_daemon_command_or_raise(action: str) -> None:
    from apps.voice.daemon_control import send_daemon_command
    if not send_daemon_command(action):
        raise HTTPException(status_code=503, detail=f"Could not dispatch voice daemon command: {action}")


class CommandRequest(BaseModel):
    """A transcript only; the backend owns the authenticated voice session."""
    model_config = ConfigDict(extra="forbid")
    text: str = Field(..., min_length=1, max_length=4096)


class VoiceSessionPinRequest(BaseModel):
    pin: str = Field(..., min_length=1, max_length=128)


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


def _daemon_snapshot():
    """Resolve the capture owner and accept only fresh daemon telemetry."""
    from apps.voice.wake_word_engine import is_voice_service_daemon_running
    from apps.voice.daemon_status import read_status
    try:
        external_owner = is_voice_service_daemon_running()
    except RuntimeError:
        external_owner = None
    return external_owner, read_status() if external_owner else None


@voice_router.get("/status")
def get_voice_status():
    """Return real-time voice pipeline state and hardware device status."""
    from apps.voice.speech_manager import speech_manager
    st = voice_service.get_state()
    external_owner, telemetry = _daemon_snapshot()
    st["capture_owner"] = "voice_daemon" if external_owner else "unknown" if external_owner is None else "backend"
    if external_owner is not False:
        st["local_state"] = st["state"]
        st["state"] = telemetry["state"] if telemetry else "EXTERNAL_OWNER"
        st["listening"] = (telemetry["is_running"] and telemetry["state"] in {"STANDBY_LISTENING", "FOLLOW_UP_STANDBY", "LISTENING_SPEECH"}) if telemetry else None
        st["muted"] = telemetry["muted"] if telemetry else None
        st["daemon_telemetry"] = telemetry
        st["wake_engine"] = telemetry or {"state": "EXTERNAL_OWNER", "is_running": None}
    diag = speech_manager.get_status()
    st["diagnostics"] = diag
    st["speaker"] = diag["speaker"]
    st["tts"] = diag["tts"]
    return st


@voice_router.get("/session")
def get_voice_session():
    """Return the local, server-owned voice identity session.

    The response intentionally distinguishes the recognized display role from
    the effective authorization role: a recognized administrator still needs a
    PIN before administrative tools become available.
    """
    from apps.voice.session_manager import voice_session_mgr
    session = voice_session_mgr.get_active_session()
    return {
        "status": "ok",
        "session": session.model_dump(),
        "authorization_role": session.authorization_role(),
    }


@voice_router.post("/session/identify")
def identify_voice_speaker():
    """Refresh the voice session from the existing camera service snapshot."""
    from apps.voice.session_manager import voice_session_mgr
    return voice_session_mgr.identify_speaker_from_camera()


@voice_router.post("/session/verify-pin")
def elevate_voice_session(req: VoiceSessionPinRequest):
    """Grant time-limited admin authority after local PIN verification."""
    from apps.voice.session_manager import voice_session_mgr
    verified, message = voice_session_mgr.verify_admin_pin(req.pin)
    if not verified:
        raise HTTPException(status_code=401, detail=message)
    session = voice_session_mgr.get_active_session()
    return {
        "status": "ok",
        "message": message,
        "session": session.model_dump(),
        "authorization_role": session.authorization_role(),
    }


@voice_router.post("/session/invalidate")
def invalidate_voice_session():
    """End the current voice identity session and return to GUEST authority."""
    from apps.voice.session_manager import voice_session_mgr
    session = voice_session_mgr.invalidate_session()
    return {
        "status": "ok",
        "session": session.model_dump(),
        "authorization_role": session.authorization_role(),
    }


@voice_router.post("/start")
def start_voice_listening():
    """Start continuous background wake-word listening loop."""
    from apps.voice.wake_word_engine import is_voice_service_daemon_running
    if is_voice_service_daemon_running():
        return {"status": "existing_owner", "message": "The dedicated voice daemon already owns the microphone."}
    voice_service.start()
    return {"status": "ok", "state": voice_service.get_state()}


@voice_router.post("/stop")
def stop_voice_listening():
    """Stop continuous background listening loop."""
    external_owner, _ = _daemon_snapshot()
    if external_owner:
        _send_daemon_command_or_raise("stop")
        return {"status": "ok", "target": "daemon", "state": "STOPPING"}
    voice_service.stop()
    return {"status": "ok", "target": "backend", "state": voice_service.get_state()}


@voice_router.post("/mute")
def mute_voice():
    """Mute microphone capture."""
    external_owner, _ = _daemon_snapshot()
    if external_owner:
        _send_daemon_command_or_raise("mute")
        return {"status": "ok", "muted": True, "target": "daemon"}
    voice_service.mute()
    return {"status": "ok", "muted": True, "target": "backend", "state": voice_service.get_state()}


@voice_router.post("/unmute")
def unmute_voice():
    """Unmute microphone capture."""
    external_owner, _ = _daemon_snapshot()
    if external_owner:
        _send_daemon_command_or_raise("unmute")
        return {"status": "ok", "muted": False, "target": "daemon"}
    voice_service.unmute()
    return {"status": "ok", "muted": False, "target": "backend", "state": voice_service.get_state()}


@voice_router.post("/interrupt")
def interrupt_speech():
    """Immediately halt any active voice playback (barge-in)."""
    try:
        from apps.voice.voice_jobs import voice_job_mgr
        voice_job_mgr.cancel_active_jobs()
    except Exception:
        pass
    external_owner, _ = _daemon_snapshot()
    if external_owner:
        try:
            from apps.voice.daemon_control import send_daemon_command
            send_daemon_command("barge_in")
        except Exception:
            pass
    voice_service.stop_playback()
    return {"status": "ok", "interrupted": True}


@voice_router.post("/listen_once")
def listen_once(req: ListenOnceRequest = ListenOnceRequest()):
    """Push-to-talk: capture audio for N seconds from ReSpeaker Lite, transcribe and process."""
    result = voice_service.listen_once(duration_secs=req.duration_secs or 4)
    return result


@voice_router.get("/jobs")
def list_voice_jobs(limit: int = 20):
    """List recent in-process voice synthesis and playback jobs."""
    from apps.voice.voice_jobs import voice_job_mgr
    return {"status": "ok", "jobs": [j.model_dump() for j in voice_job_mgr.list_jobs(limit=limit)]}


@voice_router.get("/jobs/{job_id}")
def get_voice_job(job_id: str):
    """Inspect in-process voice job status, audio URL, or error."""
    from apps.voice.voice_jobs import voice_job_mgr
    job = voice_job_mgr.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Voice job not found")
    return {"status": "ok", "job": job.model_dump()}


@voice_router.post("/jobs/{job_id}/cancel")
def cancel_voice_job(job_id: str):
    """Cancel a pending or active voice synthesis job."""
    from apps.voice.voice_jobs import voice_job_mgr
    job = voice_job_mgr.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Voice job not found")
    if job.status in {"queued", "synthesizing", "playing"}:
        cancelled = voice_service.cancel_response(job_id)
        return {"status": "ok", "job_id": job_id,
                "cancelled": bool(cancelled and cancelled.status == "cancelled")}
    return {"status": "ok", "job_id": job_id, "cancelled": False, "current_status": job.status}


@voice_router.post("/command")
def run_command(req: CommandRequest, background_tasks: BackgroundTasks = None):
    """Execute inference once and submit exactly one bounded voice reply job."""
    response = voice_service.process_command(req.text, speak=False)
    try:
        job = voice_service.enqueue_response(response, broadcast=False)
    except (RuntimeError, ValueError) as exc:
        # Inference may already have performed an action: keep its confirmed
        # response and report only delivery rejection, so callers do not replay it.
        return {"status": "ok", "response": response, "job_id": None,
                "job_status": "rejected", "audio_error": str(exc)}
    return {"status": "ok", "response": response, "job_id": job.job_id, "job_status": job.status}


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
    """Test physical speaker output with 1-second diagnostic sine tone."""
    from apps.voice.speech_manager import speech_manager
    return speech_manager.test_speaker()


class SpeakerConfirmRequest(BaseModel):
    confirmed: bool = True


@voice_router.post("/test/speaker/confirm")
def confirm_speaker_endpoint(req: SpeakerConfirmRequest):
    """User confirmation that the test sound was heard aloud through the physical speaker."""
    from apps.voice.speech_manager import speech_manager
    return speech_manager.confirm_speaker_audibility(confirmed=req.confirmed)


@voice_router.get("/diagnostics")
def get_voice_diagnostics():
    """Return comprehensive 6-component diagnostics for microphone, VAD, STT, AI, TTS, and speaker."""
    from apps.voice.speech_manager import speech_manager
    return speech_manager.run_voice_diagnostics()


@voice_router.get("/wake_status")
def get_wake_word_status():
    """Return live 12-state state machine telemetry for the background wake-word engine."""
    external_owner, telemetry = _daemon_snapshot()
    if external_owner is not False:
        return {
            **(telemetry or {"state": "EXTERNAL_OWNER", "is_running": None, "muted": None}),
            "capture_owner": "voice_daemon" if external_owner else "unknown",
            "telemetry_available": telemetry is not None,
        }
    from apps.voice.wake_word_engine import wake_word_engine
    return wake_word_engine.get_status()


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
    model_config = ConfigDict(extra="forbid")
    gradio_url: str
    session_id: Optional[str] = None
    verify: Optional[bool] = True


@voice_router.post("/colab/register")
def register_colab_url_alias(
    req: ColabVoiceRegisterRequest,
    request: Request,
    _: None = Depends(require_external_voice_control),
):
    """Alias for POST /api/integrations/omnivoice/register."""
    client_ip = request.client.host if request.client else "unknown"
    result = colab_manager.register_url(
        gradio_url=req.gradio_url,
        session_id=req.session_id,
        is_local_request=True,
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
def verify_colab_url_alias(
    gradio_url: Optional[str] = None,
    _: None = Depends(require_external_voice_control),
):
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
def start_colab_runner(_: None = Depends(require_external_voice_control)):
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
def test_colab_voice_alias(_: None = Depends(require_external_voice_control)):
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

