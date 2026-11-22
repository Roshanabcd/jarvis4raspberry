"""Core End-to-End AI Search Engine orchestrating multi-source indexing, RRF search, and answer synthesis."""

from __future__ import annotations

import hashlib
import json
import time
import urllib.request
from typing import Dict, List, Optional

from .config import AISearchConfig
from .hybrid_search import compute_embedding, hybrid_rrf_search
from .indexer import chunk_by_source_type, collect_directory_files
from .models import (
    DeleteSourceResponse,
    HealthResponse,
    IndexDirectoryRequest,
    IndexDirectoryResponse,
    IndexSourceRequest,
    SearchHistoryEntry,
    SearchHistoryResponse,
    SearchHit,
    SearchQueryRequest,
    SearchQueryResponse,
    SourceListResponse,
    SourceRecord,
    VALID_SOURCE_TYPES,
)
from .storage import SearchIndexStore


class AISearchEngine:
    """Unified semantic + lexical search across documents, terminal logs, codebases, and web knowledge."""

    def __init__(self, config: Optional[AISearchConfig] = None) -> None:
        self.config = config or AISearchConfig()
        self.store = SearchIndexStore(self.config.db_path)

    def health(self) -> HealthResponse:
        st = self.store.stats()
        return HealthResponse(
            embedding_dim=self.config.embedding_dim,
            total_sources=st["total_sources"],
            total_chunks=st["total_chunks"],
            by_source_type=st["by_source_type"],
        )

    def index_source(self, req: IndexSourceRequest) -> SourceRecord:
        stype = req.source_type.strip().lower()
        if stype not in VALID_SOURCE_TYPES:
            raise ValueError(f"Unsupported source_type '{stype}'. Choose from: {sorted(VALID_SOURCE_TYPES)}")

        raw_chunks = chunk_by_source_type(
            content=req.content,
            source_type=stype,
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap,
        )
        if not raw_chunks:
            raise ValueError("Source produced zero indexable chunks.")

        title = req.title.strip()
        uri = req.source_uri.strip() or "local://inline"
        tags = [t.strip() for t in req.tags if t.strip()]
        item_id = hashlib.sha256(f"{stype}:{uri}:{title}".encode("utf-8")).hexdigest()[:16]

        embedded: List[Dict[str, object]] = []
        for ch in raw_chunks:
            embed_text = f"{stype} {title} {ch['location']} {ch['content']}"
            embedded.append(
                {
                    "chunk_index": ch["chunk_index"],
                    "location": ch["location"],
                    "content": ch["content"],
                    "embedding": compute_embedding(embed_text, dim=self.config.embedding_dim),
                }
            )

        saved = self.store.upsert_source(
            item_id=item_id,
            source_type=stype,
            title=title,
            source_uri=uri,
            tags=tags,
            char_count=len(req.content),
            chunks=embedded,
        )
        return SourceRecord(**saved)

    def index_directory(self, req: IndexDirectoryRequest) -> IndexDirectoryResponse:
        resolved_dir, files, skipped = collect_directory_files(
            directory=req.directory,
            allowed_roots=self.config.allowed_roots,
            max_files=req.max_files,
            max_file_bytes=self.config.max_file_bytes,
        )
        indexed: List[SourceRecord] = []
        for fpath, stype, text in files:
            rel = str(fpath.relative_to(resolved_dir))
            rec = self.index_source(
                IndexSourceRequest(
                    source_type=stype,
                    title=rel,
                    source_uri=str(fpath),
                    content=text,
                    tags=list(req.tags) + [stype],
                )
            )
            indexed.append(rec)

        return IndexDirectoryResponse(
            directory=str(resolved_dir),
            indexed_files=len(indexed),
            skipped_files=skipped,
            sources=indexed,
        )

    def list_sources(self) -> SourceListResponse:
        sources = [SourceRecord(**s) for s in self.store.list_sources()]
        st = self.store.stats()
        return SourceListResponse(
            total=len(sources),
            by_source_type=st["by_source_type"],
            sources=sources,
        )

    def delete_source(self, item_id: str) -> DeleteSourceResponse:
        deleted = self.store.delete_source(item_id.strip())
        if not deleted:
            raise KeyError(f"Indexed source '{item_id}' not found.")
        return DeleteSourceResponse(deleted=True, item_id=item_id.strip())

    def _synthesize_local(self, query: str, hits: List[Dict[str, object]]) -> str:
        if not hits:
            return f"No indexed sources matched '{query}'."
        lines: List[str] = []
        for h in hits[:3]:
            lines.append(f"[{h['source_type']}: {h['title']} ({h['location']})] {h['snippet']}")
        return " | ".join(lines)

    def _synthesize_openrouter(self, query: str, hits: List[Dict[str, object]]) -> Optional[str]:
        if not self.config.openrouter_api_key or not hits:
            return None
        context = "\n\n".join(
            f"[{h['source_type']}: {h['title']} ({h['location']})]\n{h['content']}"
            for h in hits[:4]
        )
        prompt = (
            "Synthesize a concise, factual answer to the search query using ONLY the retrieved sources. "
            "Cite inline as [source_type: title].\n\n"
            f"Sources:\n{context}\n\nQuery: {query}"
        )
        payload = json.dumps(
            {
                "model": self.config.openrouter_model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
            }
        ).encode("utf-8")
        request = urllib.request.Request(
            "https://openrouter.ai/api/v1/chat/completions",
            data=payload,
            headers={
                "Authorization": f"Bearer {self.config.openrouter_api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            return str(data["choices"][0]["message"]["content"]).strip()
        except Exception:
            return None

    def query(self, req: SearchQueryRequest) -> SearchQueryResponse:
        t0 = time.perf_counter()
        valid_filters = [s.strip().lower() for s in req.source_types if s.strip().lower() in VALID_SOURCE_TYPES]
        chunks = self.store.list_chunks(source_types=valid_filters or None)

        if req.tags:
            wanted = {t.strip().lower() for t in req.tags if t.strip()}
            chunks = [c for c in chunks if wanted & {t.lower() for t in c["tags"]}]

        raw_hits = hybrid_rrf_search(
            query=req.query,
            chunks=chunks,
            dim=self.config.embedding_dim,
            rrf_k=self.config.rrf_k,
            top_k=req.top_k,
        )

        synthesis_mode = "disabled"
        synthesized = ""
        if req.synthesize_answer:
            synthesis_mode = "local_multi_source_synthesis"
            if req.synthesize_with_llm and self.config.openrouter_api_key:
                llm_ans = self._synthesize_openrouter(req.query, raw_hits)
                if llm_ans:
                    synthesized = llm_ans
                    synthesis_mode = "openrouter_synthesis"
            if not synthesized:
                synthesized = self._synthesize_local(req.query, raw_hits)

        latency_ms = round((time.perf_counter() - t0) * 1000.0, 2)
        self.store.log_query(
            query=req.query,
            source_filter=",".join(valid_filters) if valid_filters else "all",
            result_count=len(raw_hits),
            latency_ms=latency_ms,
        )

        return SearchQueryResponse(
            query=req.query,
            latency_ms=latency_ms,
            total_hits=len(raw_hits),
            synthesis_mode=synthesis_mode,
            synthesized_answer=synthesized,
            hits=[SearchHit(**h) for h in raw_hits],
        )

    def history(self, limit: int = 25) -> SearchHistoryResponse:
        rows = [SearchHistoryEntry(**r) for r in self.store.list_history(limit=limit)]
        return SearchHistoryResponse(total=len(rows), history=rows)
