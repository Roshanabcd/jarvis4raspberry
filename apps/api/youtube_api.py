"""
FastAPI Router for JARVIS YouTube AI (youtube-summarizer).

Endpoints:
- POST /api/youtube/validate-url: URL validation with strict SSRF defense.
- POST /api/youtube/metadata: Official YouTube Data API v3 metadata lookup with oEmbed fallback.
- POST /api/youtube/transcripts/upload: Ingest user-provided subtitle files (SRT, VTT, TXT, JSON).
- POST /api/youtube/transcripts/media: Local Whisper transcription for user media with confirmed rights.
- GET  /api/youtube/transcripts/{video_id}: Retrieve transcript or truthful unavailable explanation.
- POST /api/youtube/summarize: Generate summaries in any of the 12 supported formats.
- POST /api/youtube/ask: Conversational grounded Q&A with prompt injection defense.
- POST /api/youtube/notes: Save video summary and takeaways as persistent notes.
- GET  /api/youtube/notes: Search and list saved notes.
- GET  /api/youtube/notes/{note_id}: Get note details.
- DELETE /api/youtube/notes/{note_id}: Delete saved note.
- GET  /api/youtube/notes/{note_id}/export: Export note in Markdown, JSON, or Text.
- GET  /api/youtube/history: View user activity history.
- DELETE /api/youtube/history: Clear user history.
- GET  /api/youtube/config: Telemetry on API key, Whisper, and FFmpeg.
"""
import logging
import os
import shutil
import time
from typing import Any, Dict, List, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel, Field

from apps.apps_center.permissions import AppRequestIdentity, apps_permissions
from apps.youtube.database import YouTubeDatabase
from apps.youtube.indexing import TranscriptIndex, chunk_transcript
from apps.youtube.metadata import YouTubeMetadataService
from apps.youtube.models import (
    TranscriptChunk,
    TranscriptSegment,
    TranscriptSource,
    VideoNote,
    YouTubeVideoInfo,
)
from apps.youtube.qa import VideoQAAssistant
from apps.youtube.summarizer import (
    SUMMARY_TYPES,
    YouTubeSummarizer,
    extract_creator_chapters,
    generate_ai_chapters,
)
from apps.youtube.url_parser import (
    InvalidYouTubeUrlError,
    SSRFSecurityError,
    extract_video_id,
    is_valid_youtube_url,
)

logger = logging.getLogger("JARVIS.API.YouTube")

youtube_router = APIRouter(prefix="/youtube", tags=["youtube"])

_db = YouTubeDatabase()
_metadata_service = YouTubeMetadataService()
_summarizer = YouTubeSummarizer()
_qa_assistant = VideoQAAssistant()


def get_current_user_identity() -> AppRequestIdentity:
    try:
        return apps_permissions.get_current_identity()
    except Exception:
        return AppRequestIdentity(user_id="default_user", username="User", role=apps_permissions.UserRole.USER)


# ── Request / Response Models ──────────────────────────────────────

class ValidateUrlRequest(BaseModel):
    url: str


class MetadataRequest(BaseModel):
    video_id: Optional[str] = None
    url: Optional[str] = None


class TranscriptUploadRequest(BaseModel):
    video_id: str
    content: str
    filename: Optional[str] = "transcript.txt"


class MediaTranscribeRequest(BaseModel):
    video_id: str
    file_path: str
    confirm_rights: bool = False
    model_name: Optional[str] = "tiny"


class SummarizeRequest(BaseModel):
    video_id: str
    summary_type: str = "detailed"
    provider: Optional[str] = None
    auto_save_note: bool = False


class AskQuestionRequest(BaseModel):
    video_id: str
    question: str
    provider: Optional[str] = None


class SaveNoteRequest(BaseModel):
    video_id: str
    video_title: str
    channel: Optional[str] = ""
    summary_type: str
    content: str
    chapters: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    key_points: Optional[List[str]] = Field(default_factory=list)


# ── Endpoints ──────────────────────────────────────────────────────

@youtube_router.post("/validate-url")
def validate_url(req: ValidateUrlRequest):
    """
    Validate and extract 11-char video ID from YouTube URL with strict SSRF defense.
    """
    try:
        vid = extract_video_id(req.url)
        return {
            "valid": True,
            "video_id": vid,
            "canonical_url": f"https://www.youtube.com/watch?v={vid}",
            "error": None,
        }
    except SSRFSecurityError as s_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Security rejection (SSRF protection): {s_err}",
        )
    except InvalidYouTubeUrlError as val_err:
        return {
            "valid": False,
            "video_id": None,
            "canonical_url": "",
            "error": str(val_err),
        }
    except Exception as e:
        return {
            "valid": False,
            "video_id": None,
            "canonical_url": "",
            "error": f"Invalid URL: {str(e)}",
        }


@youtube_router.post("/metadata")
def get_metadata(
    req: MetadataRequest,
    identity: AppRequestIdentity = Depends(get_current_user_identity),
):
    """
    Fetch official metadata via YouTube Data API v3 or public oEmbed fallback.
    """
    vid = req.video_id
    if not vid and req.url:
        try:
            vid = extract_video_id(req.url)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid YouTube URL: {e}")

    if not vid:
        raise HTTPException(status_code=400, detail="Either 'video_id' or 'url' must be provided.")

    # Check cache first
    cached = _db.get_video(vid)
    if cached and cached.title != "YouTube Video":
        return cached.to_dict()

    try:
        info = _metadata_service.fetch_metadata(vid)
        _db.save_video(info)
        _db.record_history(
            user_id=identity.user_id,
            video_id=vid,
            action="FETCHED_METADATA",
            details={"title": info.title, "channel": info.channel_title},
        )
        return info.to_dict()
    except Exception as e:
        logger.error("Failed to fetch metadata for %s: %s", vid, e)
        raise HTTPException(status_code=500, detail=f"Error fetching metadata: {str(e)}")


@youtube_router.post("/transcripts/upload")
def upload_transcript(
    req: TranscriptUploadRequest,
    identity: AppRequestIdentity = Depends(get_current_user_identity),
):
    """
    Ingest user-provided transcript file (SRT, VTT, TXT, or JSON).
    """
    if not req.content or not req.content.strip():
        raise HTTPException(status_code=400, detail="Transcript content cannot be empty.")

    from apps.youtube.transcripts import parse_transcript_content

    segments = parse_transcript_content(req.content, filename_hint=req.filename or "")
    if not segments:
        raise HTTPException(
            status_code=400,
            detail="Failed to parse any valid subtitle segments from the provided content.",
        )

    chunks = chunk_transcript(segments=segments, video_id=req.video_id, user_id=identity.user_id)
    source_val = segments[0].source.value if hasattr(segments[0].source, "value") else str(segments[0].source)

    _db.save_transcript(
        video_id=req.video_id,
        user_id=identity.user_id,
        source=source_val,
        language="en",
        segments=segments,
        chunks=chunks,
    )

    _db.record_history(
        user_id=identity.user_id,
        video_id=req.video_id,
        action="UPLOADED_TRANSCRIPT",
        details={"segment_count": len(segments), "chunk_count": len(chunks), "source": source_val},
    )

    return {
        "status": "SUCCESS",
        "video_id": req.video_id,
        "segment_count": len(segments),
        "chunk_count": len(chunks),
        "source": source_val,
    }


@youtube_router.post("/transcripts/media")
def transcribe_media(
    req: MediaTranscribeRequest,
    identity: AppRequestIdentity = Depends(get_current_user_identity),
):
    """
    Transcribe a local audio/video file using FFmpeg and local Whisper.
    Requires explicit user rights confirmation.
    """
    if not req.confirm_rights:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Permission Denied: You must explicitly confirm ownership or processing rights "
                "for local media transcription by setting confirm_rights=true."
            ),
        )

    if not os.path.isfile(req.file_path):
        raise HTTPException(
            status_code=404, detail=f"Media file '{req.file_path}' does not exist."
        )

    from apps.youtube.transcripts import transcribe_local_media

    try:
        segments = transcribe_local_media(
            media_file_path=req.file_path,
            confirm_rights=req.confirm_rights,
            model_name=req.model_name or "tiny",
        )
        if not segments:
            raise HTTPException(status_code=500, detail="Transcription produced no segments.")

        chunks = chunk_transcript(segments=segments, video_id=req.video_id, user_id=identity.user_id)
        _db.save_transcript(
            video_id=req.video_id,
            user_id=identity.user_id,
            source=TranscriptSource.LOCAL_MEDIA_TRANSCRIPTION.value,
            language="en",
            segments=segments,
            chunks=chunks,
        )

        _db.record_history(
            user_id=identity.user_id,
            video_id=req.video_id,
            action="TRANSCRIBED_LOCAL_MEDIA",
            details={"file_path": req.file_path, "segment_count": len(segments)},
        )

        return {
            "status": "SUCCESS",
            "video_id": req.video_id,
            "segment_count": len(segments),
            "chunk_count": len(chunks),
            "source": TranscriptSource.LOCAL_MEDIA_TRANSCRIPTION.value,
        }
    except PermissionError as p_err:
        raise HTTPException(status_code=403, detail=str(p_err))
    except Exception as e:
        logger.error("Media transcription error for %s: %s", req.video_id, e)
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")


@youtube_router.get("/transcripts/{video_id}")
def get_transcript(
    video_id: str,
    identity: AppRequestIdentity = Depends(get_current_user_identity),
):
    """
    Retrieve stored transcript for video_id, or return truthful explanation if unavailable.
    """
    data = _db.get_transcript(video_id=video_id, user_id=identity.user_id)
    if not data:
        from apps.youtube.transcripts import get_transcript_unavailable_response

        return get_transcript_unavailable_response(video_id)

    return {
        "status": "AVAILABLE",
        "video_id": video_id,
        "source": data["source"],
        "language": data["language"],
        "segments": [s.to_dict() for s in data["segments"]],
        "chunks": [c.to_dict() for c in data["chunks"]],
        "created_at": data["created_at"],
    }


@youtube_router.post("/summarize")
def summarize_video(
    req: SummarizeRequest,
    identity: AppRequestIdentity = Depends(get_current_user_identity),
):
    """
    Generate summary in any of the 12 formats, extract chapters, and key information.
    """
    if req.summary_type not in SUMMARY_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid summary_type '{req.summary_type}'. Supported: {list(SUMMARY_TYPES.keys())}",
        )

    t_data = _db.get_transcript(video_id=req.video_id, user_id=identity.user_id)
    if not t_data or not t_data.get("chunks"):
        raise HTTPException(
            status_code=400,
            detail=(
                f"No transcript found for video '{req.video_id}'. "
                "Please upload a subtitle file (.srt/.vtt/.txt) or transcribe local media first."
            ),
        )

    chunks: List[TranscriptChunk] = t_data["chunks"]
    transcript_text = "\n".join(c.text for c in chunks)

    # Fetch metadata if available
    video_info = _db.get_video(req.video_id)
    video_title = video_info.title if video_info else "YouTube Video"
    channel = video_info.channel_title if video_info else ""
    description = video_info.description if video_info else ""
    duration = video_info.duration_seconds if video_info else 0

    # 1. Summarization
    summary_res = _summarizer.summarize(
        transcript_text=transcript_text,
        summary_type=req.summary_type,
        video_title=video_title,
        channel=channel,
        provider=req.provider,
    )

    # 2. Chapters (Creator-provided from description or AI-generated)
    chapters = extract_creator_chapters(description, video_id=req.video_id, video_duration=duration)
    if not chapters:
        chapters = generate_ai_chapters(chunks=chunks, video_id=req.video_id)

    # 3. Key information extraction
    key_info = _summarizer.extract_key_information(transcript_text=transcript_text, chunks=chunks)

    # Auto-save note if requested
    note_id = None
    if req.auto_save_note:
        saved_note = _db.save_note(
            VideoNote(
                note_id=f"note_{uuid.uuid4().hex[:8]}",
                user_id=identity.user_id,
                video_id=req.video_id,
                video_title=video_title,
                channel=channel,
                summary_type=req.summary_type,
                content=summary_res["content"],
                chapters=[c.to_dict() for c in chapters],
                key_points=key_info.topics,
            )
        )
        note_id = saved_note.note_id

    _db.record_history(
        user_id=identity.user_id,
        video_id=req.video_id,
        action="SUMMARIZED",
        details={"summary_type": req.summary_type, "note_id": note_id},
    )

    return {
        "video_id": req.video_id,
        "video_title": video_title,
        "channel": channel,
        "summary_type": req.summary_type,
        "format_name": summary_res["format_name"],
        "content": summary_res["content"],
        "provider": summary_res.get("provider", "ai"),
        "fallback": summary_res.get("fallback", False),
        "chapters": [c.to_dict() for c in chapters],
        "key_information": key_info.to_dict(),
        "saved_note_id": note_id,
    }


@youtube_router.post("/ask")
def ask_video_question(
    req: AskQuestionRequest,
    identity: AppRequestIdentity = Depends(get_current_user_identity),
):
    """
    Conversational grounded Q&A answering strictly from video transcript.
    """
    t_data = _db.get_transcript(video_id=req.video_id, user_id=identity.user_id)
    if not t_data or not t_data.get("chunks"):
        raise HTTPException(
            status_code=400,
            detail=(
                f"No transcript found for video '{req.video_id}'. "
                "Please upload a transcript before asking questions."
            ),
        )

    chunks: List[TranscriptChunk] = t_data["chunks"]
    index = TranscriptIndex(video_id=req.video_id, chunks=chunks)

    video_info = _db.get_video(req.video_id)
    video_title = video_info.title if video_info else "YouTube Video"

    answer = _qa_assistant.ask(
        question=req.question,
        index=index,
        video_title=video_title,
        provider=req.provider,
    )

    _db.record_history(
        user_id=identity.user_id,
        video_id=req.video_id,
        action="ASKED_QUESTION",
        details={
            "question": req.question,
            "grounded": answer.grounded,
            "timestamp": answer.timestamp,
        },
    )

    return answer.to_dict()


# ── Notes & History Endpoints ─────────────────────────────────────

@youtube_router.post("/notes")
def create_note(
    req: SaveNoteRequest,
    identity: AppRequestIdentity = Depends(get_current_user_identity),
):
    note = VideoNote(
        note_id=f"note_{uuid.uuid4().hex[:8]}",
        user_id=identity.user_id,
        video_id=req.video_id,
        video_title=req.video_title,
        channel=req.channel or "",
        summary_type=req.summary_type,
        content=req.content,
        chapters=req.chapters or [],
        key_points=req.key_points or [],
    )
    saved = _db.save_note(note)
    _db.record_history(
        user_id=identity.user_id,
        video_id=req.video_id,
        action="SAVED_NOTE",
        details={"note_id": saved.note_id, "title": saved.video_title},
    )
    return saved.to_dict()


@youtube_router.get("/notes")
def list_notes(
    query: str = Query("", description="Search term for title or content"),
    limit: int = Query(50, ge=1, le=200),
    identity: AppRequestIdentity = Depends(get_current_user_identity),
):
    notes = _db.list_notes(user_id=identity.user_id, query=query, limit=limit)
    return [n.to_dict() for n in notes]


@youtube_router.get("/notes/{note_id}")
def get_note(
    note_id: str,
    identity: AppRequestIdentity = Depends(get_current_user_identity),
):
    note = _db.get_note(note_id=note_id, user_id=identity.user_id)
    if not note:
        raise HTTPException(status_code=404, detail=f"Note '{note_id}' not found.")
    return note.to_dict()


@youtube_router.delete("/notes/{note_id}")
def delete_note(
    note_id: str,
    identity: AppRequestIdentity = Depends(get_current_user_identity),
):
    ok = _db.delete_note(note_id=note_id, user_id=identity.user_id)
    if not ok:
        raise HTTPException(status_code=404, detail=f"Note '{note_id}' not found.")
    return {"status": "SUCCESS", "deleted_note_id": note_id}


@youtube_router.get("/notes/{note_id}/export")
def export_note(
    note_id: str,
    format: str = Query("markdown", description="Export format: markdown, json, text"),
    identity: AppRequestIdentity = Depends(get_current_user_identity),
):
    try:
        content = _db.export_note(note_id=note_id, user_id=identity.user_id, export_format=format)
        media_type = "text/markdown" if format == "markdown" else ("application/json" if format == "json" else "text/plain")
        return Response(content=content, media_type=media_type)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Note '{note_id}' not found.")


@youtube_router.get("/history")
def get_history(
    limit: int = Query(50, ge=1, le=100),
    identity: AppRequestIdentity = Depends(get_current_user_identity),
):
    return _db.get_history(user_id=identity.user_id, limit=limit)


@youtube_router.delete("/history")
def clear_history(
    identity: AppRequestIdentity = Depends(get_current_user_identity),
):
    _db.clear_history(user_id=identity.user_id)
    return {"status": "SUCCESS", "message": "History cleared successfully."}


@youtube_router.get("/config")
def get_youtube_config():
    """
    Return truthful configuration and tool telemetry.
    """
    api_configured = _metadata_service.is_api_configured()
    whisper_avail = False
    try:
        import whisper
        whisper_avail = True
    except ImportError:
        pass

    ffmpeg_avail = bool(shutil.which("ffmpeg"))

    return {
        "youtube_api_configured": api_configured,
        "whisper_available": whisper_avail,
        "ffmpeg_available": ffmpeg_avail,
        "supported_summary_types": SUMMARY_TYPES,
        "status": "ready",
    }
