"""
Authorized Transcript Ingestion, Parsing, and Local Media Processing.

Strict Policy Adherence:
- Zero unauthorized scraping or downloading from YouTube.
- Supports authorized user-uploaded transcripts (SRT, VTT, TXT, JSON).
- Supports official YouTube Data API v3 OAuth download for creator-owned captions.
- Supports local media transcription (FFmpeg + Whisper) for user-uploaded audio/video
  with explicit user-confirmed processing rights.
- Provides truthful, transparent messaging when transcript access is unavailable.
"""
import io
import json
import logging
import os
import re
import shutil
import subprocess
import tempfile
from typing import Any, Dict, List, Optional, Tuple, Union

from .models import TranscriptSegment, TranscriptSource

logger = logging.getLogger("JARVIS.YouTube.Transcripts")

# Regex patterns for subtitle formats
_HTML_TAG_RE = re.compile(r"<[^>]+>")
_SPEAKER_RE = re.compile(r"^(?:<v\s+([^>]+)>|\[([^\]]+)\]|([A-Za-z0-9 _\-]+):)\s*(.*)", re.DOTALL)
_TIMESTAMP_LINE_RE = re.compile(
    r"^(?:\[?(\d{1,2}:\d{2}(?::\d{2})?(?:[,\.]\d{1,3})?)\]?)\s*[-:]?\s*(.*)$"
)


def clean_subtitle_text(raw_text: str) -> Tuple[Optional[str], str]:
    """
    Remove HTML tags and extract speaker prefix if present.
    Returns: (speaker, cleaned_text)
    """
    cleaned = raw_text.strip()
    speaker = None

    # Check for <v Speaker> first before stripping HTML tags
    v_match = re.match(r"^<v\s+([^>]+)>(.*?)(?:</v>)?$", cleaned, re.DOTALL)
    if v_match:
        speaker = v_match.group(1).strip()
        cleaned = v_match.group(2).strip()

    # Now strip remaining HTML tags
    cleaned = _HTML_TAG_RE.sub("", cleaned).strip()

    # Check for [Speaker]: or Speaker:
    spk_match = re.match(r"^(?:\[([^\]]+)\]:?|([A-Za-z0-9 _\-]+):)\s*(.*)", cleaned, re.DOTALL)
    if spk_match and not speaker:
        spk = spk_match.group(1) or spk_match.group(2)
        rest = spk_match.group(3).strip()
        if rest.startswith(":"):
            rest = rest[1:].strip()
        if spk and len(spk) < 50:
            speaker = spk.strip()
            cleaned = rest

    return speaker, cleaned


def parse_timestamp_to_seconds(ts_str: str) -> float:
    """
    Convert timestamps like '01:23:45,678' or '00:01:23.456' or '01:23' into seconds.
    """
    cleaned = ts_str.strip().replace(",", ".")
    parts = cleaned.split(":")
    if len(parts) == 3:
        h = float(parts[0])
        m = float(parts[1])
        s = float(parts[2])
        return h * 3600.0 + m * 60.0 + s
    elif len(parts) == 2:
        m = float(parts[0])
        s = float(parts[1])
        return m * 60.0 + s
    elif len(parts) == 1:
        return float(parts[0])
    return 0.0


def parse_srt(content: str) -> List[TranscriptSegment]:
    """
    Parse an SRT (SubRip) subtitle string into a list of TranscriptSegments.
    """
    segments: List[TranscriptSegment] = []
    blocks = re.split(r"\n\s*\n", content.strip())
    segment_idx = 1

    time_pattern = re.compile(
        r"(\d{1,2}:\d{2}:\d{2}[,\.]\d{1,3})\s*-->\s*(\d{1,2}:\d{2}:\d{2}[,\.]\d{1,3})"
    )

    for block in blocks:
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if not lines:
            continue

        time_line_idx = -1
        start_sec, end_sec = 0.0, 0.0

        for idx, line in enumerate(lines):
            match = time_pattern.search(line)
            if match:
                time_line_idx = idx
                start_sec = parse_timestamp_to_seconds(match.group(1))
                end_sec = parse_timestamp_to_seconds(match.group(2))
                break

        if time_line_idx == -1:
            continue

        text_lines = lines[time_line_idx + 1 :]
        raw_text = " ".join(text_lines)
        speaker, text = clean_subtitle_text(raw_text)

        if text:
            segments.append(
                TranscriptSegment(
                    segment_id=segment_idx,
                    start=start_sec,
                    end=end_sec,
                    text=text,
                    speaker=speaker,
                    source=TranscriptSource.USER_UPLOADED_SRT,
                )
            )
            segment_idx += 1

    return segments


def parse_vtt(content: str) -> List[TranscriptSegment]:
    """
    Parse a WebVTT subtitle string into a list of TranscriptSegments.
    """
    segments: List[TranscriptSegment] = []
    lines = content.strip().splitlines()
    segment_idx = 1

    # Skip header
    idx = 0
    while idx < len(lines):
        line = lines[idx].strip()
        idx += 1
        if line.startswith("WEBVTT"):
            break

    time_pattern = re.compile(
        r"((?:\d{1,2}:)?\d{2}:\d{2}[,\.]\d{1,3})\s*-->\s*((?:\d{1,2}:)?\d{2}:\d{2}[,\.]\d{1,3})"
    )

    current_start = 0.0
    current_end = 0.0
    current_text_lines: List[str] = []
    in_cue = False

    while idx < len(lines):
        line = lines[idx].strip()
        idx += 1

        if not line:
            if in_cue and current_text_lines:
                raw_text = " ".join(current_text_lines)
                speaker, text = clean_subtitle_text(raw_text)
                if text:
                    segments.append(
                        TranscriptSegment(
                            segment_id=segment_idx,
                            start=current_start,
                            end=current_end,
                            text=text,
                            speaker=speaker,
                            source=TranscriptSource.USER_UPLOADED_VTT,
                        )
                    )
                    segment_idx += 1
                current_text_lines = []
                in_cue = False
            continue

        # Check for timing line
        match = time_pattern.search(line)
        if match:
            # If we had a previous cue without blank line separator
            if in_cue and current_text_lines:
                raw_text = " ".join(current_text_lines)
                speaker, text = clean_subtitle_text(raw_text)
                if text:
                    segments.append(
                        TranscriptSegment(
                            segment_id=segment_idx,
                            start=current_start,
                            end=current_end,
                            text=text,
                            speaker=speaker,
                            source=TranscriptSource.USER_UPLOADED_VTT,
                        )
                    )
                    segment_idx += 1
                current_text_lines = []

            current_start = parse_timestamp_to_seconds(match.group(1))
            current_end = parse_timestamp_to_seconds(match.group(2))
            in_cue = True
        elif in_cue:
            current_text_lines.append(line)

    # Final cue flush
    if in_cue and current_text_lines:
        raw_text = " ".join(current_text_lines)
        speaker, text = clean_subtitle_text(raw_text)
        if text:
            segments.append(
                TranscriptSegment(
                    segment_id=segment_idx,
                    start=current_start,
                    end=current_end,
                    text=text,
                    speaker=speaker,
                    source=TranscriptSource.USER_UPLOADED_VTT,
                )
            )

    return segments


def parse_txt(content: str) -> List[TranscriptSegment]:
    """
    Parse a plain text transcript, which may optionally contain timestamps per line
    or paragraph format.
    """
    segments: List[TranscriptSegment] = []
    lines = [line.strip() for line in content.splitlines() if line.strip()]
    if not lines:
        return []

    segment_idx = 1
    has_timestamps = any(_TIMESTAMP_LINE_RE.match(line) for line in lines[:10])

    if has_timestamps:
        last_start = 0.0
        for line in lines:
            m = _TIMESTAMP_LINE_RE.match(line)
            if m:
                ts_str = m.group(1)
                text_part = m.group(2).strip()
                start_sec = parse_timestamp_to_seconds(ts_str)
                speaker, text = clean_subtitle_text(text_part)
                if text:
                    segments.append(
                        TranscriptSegment(
                            segment_id=segment_idx,
                            start=start_sec,
                            end=start_sec + 5.0,  # Estimated duration
                            text=text,
                            speaker=speaker,
                            source=TranscriptSource.USER_UPLOADED_TXT,
                        )
                    )
                    segment_idx += 1
                    last_start = start_sec
            else:
                # Continuation text for previous segment
                if segments:
                    segments[-1].text += " " + line
                else:
                    speaker, text = clean_subtitle_text(line)
                    segments.append(
                        TranscriptSegment(
                            segment_id=segment_idx,
                            start=0.0,
                            end=5.0,
                            text=text,
                            speaker=speaker,
                            source=TranscriptSource.USER_UPLOADED_TXT,
                        )
                    )
                    segment_idx += 1
    else:
        # Paragraph-based segmentation
        paragraphs = re.split(r"\n\s*\n", content.strip())
        current_time = 0.0
        for p in paragraphs:
            clean_p = " ".join(p.split())
            if not clean_p:
                continue
            speaker, text = clean_subtitle_text(clean_p)
            word_count = len(text.split())
            duration = max(3.0, word_count * 0.4)  # ~150 words per minute
            segments.append(
                TranscriptSegment(
                    segment_id=segment_idx,
                    start=current_time,
                    end=current_time + duration,
                    text=text,
                    speaker=speaker,
                    source=TranscriptSource.USER_UPLOADED_TXT,
                )
            )
            segment_idx += 1
            current_time += duration

    return segments


def parse_json(content: str) -> List[TranscriptSegment]:
    """
    Parse JSON formatted transcripts:
    Supports list of segment dicts, or dict with 'segments' / 'transcript' key.
    """
    segments: List[TranscriptSegment] = []
    data = json.loads(content)
    raw_list: List[Dict[str, Any]] = []

    if isinstance(data, list):
        raw_list = data
    elif isinstance(data, dict):
        if "segments" in data and isinstance(data["segments"], list):
            raw_list = data["segments"]
        elif "transcript" in data and isinstance(data["transcript"], list):
            raw_list = data["transcript"]
        elif "items" in data and isinstance(data["items"], list):
            raw_list = data["items"]

    segment_idx = 1
    for item in raw_list:
        if not isinstance(item, dict):
            continue
        start = float(item.get("start", item.get("start_time", 0.0)))
        end = float(item.get("end", item.get("end_time", start + 3.0)))
        text = str(item.get("text", item.get("content", ""))).strip()
        speaker = item.get("speaker")
        confidence = float(item["confidence"]) if "confidence" in item else None

        if text:
            segments.append(
                TranscriptSegment(
                    segment_id=segment_idx,
                    start=start,
                    end=end,
                    text=text,
                    speaker=speaker,
                    source=TranscriptSource.USER_UPLOADED_JSON,
                    confidence=confidence,
                )
            )
            segment_idx += 1

    return segments


def parse_transcript_content(content: str, filename_hint: str = "") -> List[TranscriptSegment]:
    """
    Auto-detect format and parse transcript content.
    """
    hint = filename_hint.lower()
    stripped = content.strip()

    if hint.endswith(".srt") or (re.search(r"\d{1,2}:\d{2}:\d{2}[,\.]\d{1,3}\s*-->", stripped) and not stripped.startswith("WEBVTT")):
        return parse_srt(content)
    elif hint.endswith(".vtt") or stripped.startswith("WEBVTT"):
        return parse_vtt(content)
    elif hint.endswith(".json") or (stripped.startswith("[") or stripped.startswith("{")):
        try:
            return parse_json(content)
        except Exception:
            pass  # Fall through to txt if JSON parsing fails

    return parse_txt(content)


def transcribe_local_media(
    media_file_path: str,
    confirm_rights: bool = False,
    model_name: str = "tiny",
    whisper_engine: Optional[Any] = None,
) -> List[TranscriptSegment]:
    """
    Transcribe a local media file (audio/video) using FFmpeg and local Whisper.

    Legal & Policy Gate:
    - User must explicitly pass `confirm_rights=True` indicating they own
      or have explicit rights to process this media file.
    """
    if not confirm_rights:
        raise PermissionError(
            "User must explicitly confirm ownership or processing rights for local media transcription."
        )

    if not os.path.isfile(media_file_path):
        raise FileNotFoundError(f"Media file '{media_file_path}' does not exist.")

    # 1. Convert to 16kHz mono WAV using ffmpeg
    temp_dir = tempfile.mkdtemp(prefix="jarvis_yt_media_")
    wav_path = os.path.join(temp_dir, "extracted_audio.wav")

    try:
        ffmpeg_cmd = [
            "/usr/bin/ffmpeg",
            "-y",
            "-i",
            media_file_path,
            "-vn",
            "-acodec",
            "pcm_s16le",
            "-ar",
            "16000",
            "-ac",
            "1",
            wav_path,
        ]
        proc = subprocess.run(ffmpeg_cmd, capture_output=True, text=True, timeout=120)
        if proc.returncode != 0 or not os.path.exists(wav_path):
            raise RuntimeError(f"FFmpeg audio extraction failed: {proc.stderr[:300]}")

        # 2. Transcribe via Whisper
        segments: List[TranscriptSegment] = []
        if whisper_engine is not None:
            result = whisper_engine.transcribe(wav_path)
        else:
            try:
                import whisper
                model = whisper.load_model(model_name)
                result = model.transcribe(wav_path)
            except ImportError:
                raise RuntimeError("OpenAI Whisper is not installed in the active environment.")

        raw_segments = result.get("segments", [])
        if raw_segments:
            for idx, s in enumerate(raw_segments, start=1):
                segments.append(
                    TranscriptSegment(
                        segment_id=idx,
                        start=float(s.get("start", 0.0)),
                        end=float(s.get("end", 0.0)),
                        text=str(s.get("text", "")).strip(),
                        source=TranscriptSource.LOCAL_MEDIA_TRANSCRIPTION,
                    )
                )
        else:
            full_text = str(result.get("text", "")).strip()
            if full_text:
                segments = parse_txt(full_text)
                for s in segments:
                    s.source = TranscriptSource.LOCAL_MEDIA_TRANSCRIPTION

        return segments
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def download_youtube_captions_oauth(
    video_id: str,
    credentials: Any,
    language: str = "en",
) -> List[TranscriptSegment]:
    """
    Download creator-owned captions using official Google YouTube Data API v3 OAuth.
    Only functions for videos owned by the authenticated account.
    """
    try:
        from googleapiclient.discovery import build
    except ImportError:
        raise RuntimeError("google-api-python-client is not installed.")

    youtube = build("youtube", "v3", credentials=credentials)
    caption_list = youtube.captions().list(part="snippet", videoId=video_id).execute()
    items = caption_list.get("items", [])
    if not items:
        raise ValueError(f"No caption tracks found for creator-owned video {video_id}.")

    # Find matching language track
    target_caption_id = None
    for item in items:
        snippet = item.get("snippet", {})
        if snippet.get("language", "").startswith(language):
            target_caption_id = item.get("id")
            break

    if not target_caption_id:
        target_caption_id = items[0].get("id")

    # Download SRT
    download_req = youtube.captions().download(id=target_caption_id, tfmt="srt")
    content = download_req.execute().decode("utf-8", errors="replace")
    segments = parse_srt(content)
    for s in segments:
        s.source = TranscriptSource.CREATOR_OWNED_CAPTIONS
    return segments


def get_transcript_unavailable_response(video_id: str) -> Dict[str, Any]:
    """
    Returns standard transparent explanation when authorized transcript is unavailable.
    """
    return {
        "status": "TRANSCRIPT_UNAVAILABLE",
        "video_id": video_id,
        "message": "Transcript access is unavailable for this video through the currently configured authorized sources.",
        "policy_explanation": (
            "In strict compliance with YouTube Terms of Service and developer guidelines, "
            "JARVIS does not perform unauthorized web scraping, unofficial API extraction, or automated video downloading."
        ),
        "authorized_options": [
            {
                "option": "upload_subtitle_file",
                "label": "Upload Subtitle File (.srt, .vtt, .json)",
                "description": "Upload a creator-provided or downloaded subtitle file.",
            },
            {
                "option": "paste_text_notes",
                "label": "Provide Transcript / Notes Text",
                "description": "Paste video notes or manual transcription directly.",
            },
            {
                "option": "upload_local_media",
                "label": "Transcribe Local Media File",
                "description": "Provide a local media file with confirmed processing rights for offline Whisper transcription.",
            },
            {
                "option": "creator_oauth",
                "label": "Connect YouTube Creator Account",
                "description": "If you are the channel owner, link OAuth credentials to access private caption tracks.",
            },
        ],
    }
