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
    res = speech_manager.synthesize_and_stage(req.text, play_system=True)
    return res


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
