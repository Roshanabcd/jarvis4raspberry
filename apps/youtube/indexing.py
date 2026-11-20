"""
Timestamp-Aware Transcript Chunking and Hybrid Semantic/Keyword Search Index.

Features:
- Sentence/segment boundary preservation during chunking.
- Exact start and end timestamp preservation for every chunk.
- Speaker attribution tracking.
- TF-IDF vectorization and cosine similarity semantic search.
- Inverted token index for exact keyword matching and hybrid ranking.
"""
import logging
import math
import re
from typing import Any, Dict, List, Optional, Set, Tuple
import uuid

from .models import TranscriptChunk, TranscriptSegment

logger = logging.getLogger("JARVIS.YouTube.Indexing")

_WORD_RE = re.compile(r"[a-zA-Z0-9_\-]+")


def tokenize(text: str) -> List[str]:
    """Tokenize text into lowercase alphanumeric tokens."""
    return [w.lower() for w in _WORD_RE.findall(text) if len(w) > 1]


def chunk_transcript(
    segments: List[TranscriptSegment],
    video_id: str,
    user_id: str = "default_user",
    target_words: int = 180,
    max_words: int = 300,
) -> List[TranscriptChunk]:
    """
    Group sequential TranscriptSegments into timestamp-aware TranscriptChunks.
    Preserves exact start timestamp from the first segment and end timestamp
    from the last segment in each chunk.
    """
    if not segments:
        return []

    # Ensure segments are sorted by start time
    sorted_segments = sorted(segments, key=lambda s: s.start)
    chunks: List[TranscriptChunk] = []

    current_segments: List[TranscriptSegment] = []
    current_word_count = 0
    chunk_index = 0

    for seg in sorted_segments:
        text = seg.text.strip()
        if not text:
            continue

        words = text.split()
        seg_word_count = len(words)

        # If adding this segment exceeds target and we already have content
        if (current_word_count + seg_word_count > target_words) and current_segments:
            # Finalize current chunk
            chunk_text = " ".join(s.text.strip() for s in current_segments)
            first_seg = current_segments[0]
            last_seg = current_segments[-1]

            # Collect unique speakers
            speakers = list(dict.fromkeys(s.speaker for s in current_segments if s.speaker))
            primary_speaker = ", ".join(speakers) if speakers else None

            chunks.append(
                TranscriptChunk(
                    chunk_id=f"chk_{video_id}_{chunk_index}_{uuid.uuid4().hex[:6]}",
                    video_id=video_id,
                    user_id=user_id,
                    chunk_index=chunk_index,
                    start=first_seg.start,
                    end=last_seg.end,
                    text=chunk_text,
                    source=first_seg.source.value if hasattr(first_seg.source, "value") else str(first_seg.source),
                    speaker=primary_speaker,
                )
            )
            chunk_index += 1
            current_segments = []
            current_word_count = 0

        current_segments.append(seg)
        current_word_count += seg_word_count

    # Final chunk
    if current_segments:
        chunk_text = " ".join(s.text.strip() for s in current_segments)
        first_seg = current_segments[0]
        last_seg = current_segments[-1]

        speakers = list(dict.fromkeys(s.speaker for s in current_segments if s.speaker))
        primary_speaker = ", ".join(speakers) if speakers else None

        chunks.append(
            TranscriptChunk(
                chunk_id=f"chk_{video_id}_{chunk_index}_{uuid.uuid4().hex[:6]}",
                video_id=video_id,
                user_id=user_id,
                chunk_index=chunk_index,
                start=first_seg.start,
                end=last_seg.end,
                text=chunk_text,
                source=first_seg.source.value if hasattr(first_seg.source, "value") else str(first_seg.source),
                speaker=primary_speaker,
            )
        )

    return chunks


class TranscriptIndex:
    """
    Search index for a video's transcript chunks.
    Combines TF-IDF vector ranking with keyword frequency matching.
    """

    def __init__(self, video_id: str, chunks: List[TranscriptChunk]):
        self.video_id = video_id
        self.chunks = chunks
        self._doc_tokens: List[List[str]] = []
        self._inverted_index: Dict[str, Set[int]] = {}
        self._idf: Dict[str, float] = {}
        self._build_index()

    def _build_index(self):
        n_docs = len(self.chunks)
        if n_docs == 0:
            return

        df: Dict[str, int] = {}
        for idx, chunk in enumerate(self.chunks):
            tokens = tokenize(chunk.text)
            self._doc_tokens.append(tokens)
            unique_tokens = set(tokens)

            for token in unique_tokens:
                if token not in self._inverted_index:
                    self._inverted_index[token] = set()
                self._inverted_index[token].add(idx)
                df[token] = df.get(token, 0) + 1

        # Calculate IDF: smooth idf = log((N + 1) / (DF + 1)) + 1
        for token, doc_freq in df.items():
            self._idf[token] = math.log((n_docs + 1.0) / (doc_freq + 1.0)) + 1.0

    def _vectorize(self, tokens: List[str]) -> Dict[str, float]:
        """Compute normalized TF-IDF vector for tokens."""
        tf: Dict[str, float] = {}
        for t in tokens:
            tf[t] = tf.get(t, 0.0) + 1.0

        vec: Dict[str, float] = {}
        for t, count in tf.items():
            idf = self._idf.get(t, 1.0)
            vec[t] = (1.0 + math.log(count)) * idf

        norm = math.sqrt(sum(v * v for v in vec.values()))
        if norm > 0:
            return {t: v / norm for t, v in vec.items()}
        return vec

    def search(
        self,
        query: str,
        top_k: int = 5,
        min_score: float = 0.02,
    ) -> List[Dict[str, Any]]:
        """
        Search chunks using hybrid TF-IDF cosine similarity and term overlap.
        Returns ordered list of dicts with:
        {
            "chunk": TranscriptChunk,
            "score": float,
            "matched_terms": List[str],
            "snippet": str,
            "start": float,
            "end": float,
            "start_formatted": str,
            "end_formatted": str,
        }
        """
        q_tokens = tokenize(query)
        if not q_tokens or not self.chunks:
            return []

        q_vec = self._vectorize(q_tokens)
        matched_chunk_indices: Set[int] = set()

        for t in q_tokens:
            if t in self._inverted_index:
                matched_chunk_indices.update(self._inverted_index[t])

        # If no exact token matches, compute similarity across all chunks
        candidates = list(matched_chunk_indices) if matched_chunk_indices else list(range(len(self.chunks)))

        results = []
        for idx in candidates:
            chunk = self.chunks[idx]
            doc_tokens = self._doc_tokens[idx]
            d_vec = self._vectorize(doc_tokens)

            # Cosine similarity
            dot_product = sum(q_vec[t] * d_vec.get(t, 0.0) for t in q_vec if t in d_vec)

            # Keyword coverage bonus
            overlap = [t for t in set(q_tokens) if t in self._inverted_index and idx in self._inverted_index[t]]
            coverage_ratio = len(overlap) / max(1, len(set(q_tokens)))

            combined_score = (dot_product * 0.7) + (coverage_ratio * 0.3)

            if combined_score >= min_score or (coverage_ratio > 0):
                results.append({
                    "chunk": chunk,
                    "score": round(float(combined_score), 4),
                    "matched_terms": overlap,
                    "snippet": chunk.text[:250] + ("..." if len(chunk.text) > 250 else ""),
                    "start": chunk.start,
                    "end": chunk.end,
                    "start_formatted": chunk.start_formatted,
                    "end_formatted": chunk.end_formatted,
                    "speaker": chunk.speaker,
                })

        results.sort(key=lambda r: r["score"], reverse=True)
        return results[:top_k]

    def get_chunks_for_time_range(self, start: float, end: float) -> List[TranscriptChunk]:
        """Return all chunks that overlap with the given time window."""
        return [
            c for c in self.chunks
            if not (c.end < start or c.start > end)
        ]

    def get_context_around_timestamp(self, timestamp: float, window_seconds: float = 30.0) -> List[TranscriptChunk]:
        """Return chunks within window_seconds of the target timestamp."""
        start = max(0.0, timestamp - window_seconds)
        end = timestamp + window_seconds
        return self.get_chunks_for_time_range(start, end)

    def get_full_transcript_text(self) -> str:
        """Return concatenated full transcript text."""
        return "\n\n".join(
            f"[{c.start_formatted} - {c.end_formatted}] {c.speaker + ': ' if c.speaker else ''}{c.text}"
            for c in self.chunks
        )
