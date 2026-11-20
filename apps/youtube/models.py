"""
Data models and enumerations for JARVIS YouTube AI.
"""
from dataclasses import dataclass, field
from enum import Enum
import time
from typing import Any, Dict, List, Optional
import uuid


class TranscriptSource(str, Enum):
    USER_UPLOADED_SRT = "user_uploaded_srt"
    USER_UPLOADED_VTT = "user_uploaded_vtt"
    USER_UPLOADED_TXT = "user_uploaded_txt"
    USER_UPLOADED_JSON = "user_uploaded_json"
    CREATOR_OWNED_CAPTIONS = "creator_owned_captions"
    LOCAL_MEDIA_TRANSCRIPTION = "local_media_transcription"
    UNAVAILABLE = "unavailable"


class ChapterSource(str, Enum):
    CREATOR_PROVIDED_CHAPTER = "creator_provided_chapter"
    AI_GENERATED_CHAPTER = "ai_generated_chapter"


class ProcessingState(str, Enum):
    READY = "READY"
    VALIDATING = "VALIDATING"
    FETCHING_METADATA = "FETCHING_METADATA"
    CHECKING_TRANSCRIPT_ACCESS = "CHECKING_TRANSCRIPT_ACCESS"
    TRANSCRIBING_USER_MEDIA = "TRANSCRIBING_USER_MEDIA"
    PROCESSING_TRANSCRIPT = "PROCESSING_TRANSCRIPT"
    GENERATING_SUMMARY = "GENERATING_SUMMARY"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    TRANSCRIPT_UNAVAILABLE = "TRANSCRIPT_UNAVAILABLE"
    WAITING_FOR_USER = "WAITING_FOR_USER"


@dataclass
class YouTubeVideoInfo:
    video_id: str
    url: str
    title: str = "YouTube Video"
    channel_title: str = "Unknown Channel"
    channel_id: Optional[str] = None
    duration_seconds: int = 0
    duration_formatted: str = "00:00"
    thumbnail_url: str = ""
    published_at: Optional[str] = None
    description: str = ""
    captions_available: bool = False
    metadata_source: str = "unauthenticated_oembed"
    embed_permitted: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "video_id": self.video_id,
            "url": self.url,
            "title": self.title,
            "channel_title": self.channel_title,
            "channel_id": self.channel_id,
            "duration_seconds": self.duration_seconds,
            "duration_formatted": self.duration_formatted,
            "thumbnail_url": self.thumbnail_url or f"https://i.ytimg.com/vi/{self.video_id}/hqdefault.jpg",
            "published_at": self.published_at,
            "description": self.description[:500],
            "captions_available": self.captions_available,
            "metadata_source": self.metadata_source,
            "embed_permitted": self.embed_permitted,
        }


@dataclass
class TranscriptSegment:
    segment_id: int
    start: float  # Start time in seconds
    end: float    # End time in seconds
    text: str
    speaker: Optional[str] = None
    source: TranscriptSource = TranscriptSource.USER_UPLOADED_TXT
    language: str = "en"
    confidence: Optional[float] = None

    @property
    def start_formatted(self) -> str:
        s = int(self.start)
        m, sec = divmod(s, 60)
        h, m = divmod(m, 60)
        return f"{h:02d}:{m:02d}:{sec:02d}" if h > 0 else f"{m:02d}:{sec:02d}"

    @property
    def end_formatted(self) -> str:
        s = int(self.end)
        m, sec = divmod(s, 60)
        h, m = divmod(m, 60)
        return f"{h:02d}:{m:02d}:{sec:02d}" if h > 0 else f"{m:02d}:{sec:02d}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "segment_id": self.segment_id,
            "start": round(self.start, 2),
            "end": round(self.end, 2),
            "start_formatted": self.start_formatted,
            "end_formatted": self.end_formatted,
            "text": self.text,
            "speaker": self.speaker,
            "source": self.source.value if isinstance(self.source, TranscriptSource) else self.source,
            "language": self.language,
            "confidence": self.confidence,
        }


@dataclass
class TranscriptChunk:
    chunk_id: str
    video_id: str
    user_id: str
    chunk_index: int
    start: float
    end: float
    text: str
    source: str
    speaker: Optional[str] = None
    start_formatted: str = ""
    end_formatted: str = ""

    def __post_init__(self):
        if not self.start_formatted:
            s = int(self.start)
            m, sec = divmod(s, 60)
            h, m = divmod(m, 60)
            self.start_formatted = f"{h:02d}:{m:02d}:{sec:02d}" if h > 0 else f"{m:02d}:{sec:02d}"
        if not self.end_formatted:
            s = int(self.end)
            m, sec = divmod(s, 60)
            h, m = divmod(m, 60)
            self.end_formatted = f"{h:02d}:{m:02d}:{sec:02d}" if h > 0 else f"{m:02d}:{sec:02d}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "video_id": self.video_id,
            "user_id": self.user_id,
            "chunk_index": self.chunk_index,
            "start": round(self.start, 2),
            "end": round(self.end, 2),
            "start_formatted": self.start_formatted,
            "end_formatted": self.end_formatted,
            "text": self.text,
            "source": self.source,
            "speaker": self.speaker,
        }


@dataclass
class VideoChapter:
    chapter_index: int
    title: str
    start_time: float
    end_time: float
    summary: str
    source: ChapterSource = ChapterSource.AI_GENERATED_CHAPTER
    video_id: str = ""

    @property
    def start_formatted(self) -> str:
        s = int(self.start_time)
        m, sec = divmod(s, 60)
        h, m = divmod(m, 60)
        return f"{h:02d}:{m:02d}:{sec:02d}" if h > 0 else f"{m:02d}:{sec:02d}"

    @property
    def youtube_url(self) -> str:
        if self.video_id:
            return f"https://www.youtube.com/watch?v={self.video_id}&t={int(self.start_time)}s"
        return f"?t={int(self.start_time)}s"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chapter_index": self.chapter_index,
            "title": self.title,
            "start_time": round(self.start_time, 2),
            "end_time": round(self.end_time, 2),
            "start_formatted": self.start_formatted,
            "summary": self.summary,
            "source": self.source.value if isinstance(self.source, ChapterSource) else self.source,
            "youtube_url": self.youtube_url,
        }


@dataclass
class KeyInformation:
    topics: List[str] = field(default_factory=list)
    concepts: List[Dict[str, str]] = field(default_factory=list)  # {"term": ..., "definition": ...}
    terminology: List[str] = field(default_factory=list)
    facts: List[Dict[str, Any]] = field(default_factory=list)     # {"fact": ..., "timestamp": ...}
    dates_and_numbers: List[Dict[str, Any]] = field(default_factory=list)
    action_items: List[str] = field(default_factory=list)
    quotes: List[Dict[str, Any]] = field(default_factory=list)    # {"quote": ..., "timestamp": ...}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "topics": self.topics,
            "concepts": self.concepts,
            "terminology": self.terminology,
            "facts": self.facts,
            "dates_and_numbers": self.dates_and_numbers,
            "action_items": self.action_items,
            "quotes": self.quotes,
        }


@dataclass
class VideoAnswer:
    question: str
    answer: str
    timestamp: Optional[float] = None
    timestamp_formatted: str = ""
    supporting_passage: str = ""
    video_title: str = ""
    source: str = ""
    confidence: float = 1.0
    grounded: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "question": self.question,
            "answer": self.answer,
            "timestamp": round(self.timestamp, 2) if self.timestamp is not None else None,
            "timestamp_formatted": self.timestamp_formatted,
            "supporting_passage": self.supporting_passage,
            "video_title": self.video_title,
            "source": self.source,
            "confidence": round(self.confidence, 2),
            "grounded": self.grounded,
        }


@dataclass
class VideoNote:
    note_id: str
    user_id: str
    video_id: str
    video_title: str
    channel: str
    summary_type: str
    content: str
    chapters: List[Dict[str, Any]] = field(default_factory=list)
    key_points: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "note_id": self.note_id,
            "user_id": self.user_id,
            "video_id": self.video_id,
            "video_title": self.video_title,
            "channel": self.channel,
            "summary_type": self.summary_type,
            "content": self.content,
            "chapters": self.chapters,
            "key_points": self.key_points,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
