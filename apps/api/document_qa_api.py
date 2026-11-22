"""
FastAPI REST API Router for JARVIS Document AI (document-qa).

Mounted at /api/document-qa/*.
Endpoints:
- POST   /api/document-qa/upload       : Upload and index a document (PDF, DOCX, TXT, MD, CSV)
- GET    /api/document-qa/documents    : List user's documents
- GET    /api/document-qa/documents/{id}: Get document details and chunks
- DELETE /api/document-qa/documents/{id}: Delete document, chunks, and storage file
- POST   /api/document-qa/search       : Hybrid semantic & keyword search across documents
- POST   /api/document-qa/ask          : Grounded Q&A with verifiable citations
- POST   /api/document-qa/summarize    : Multi-format document summarization
- GET    /api/document-qa/collections  : List user collections
- POST   /api/document-qa/collections  : Create new collection
- GET    /api/document-qa/status       : Telemetry, index stats, and supported formats
"""
from __future__ import annotations

import logging
import os
import shutil
import time
from typing import Any, Dict, List, Optional
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from pydantic import BaseModel, Field

from apps.apps_center.permissions import AppRequestIdentity, UserRole, apps_permissions
from apps.document_qa.chunking import chunk_document
from apps.document_qa.database import db as doc_db
from apps.document_qa.extractor import extractor, sanitize_filename
from apps.document_qa.indexing import document_index
from apps.document_qa.models import (
    AskDocumentRequest,
    CreateCollectionRequest,
    DocumentAnswer,
    DocumentCollection,
    DocumentMetadata,
    DocumentSummary,
    DocumentType,
    SearchDocumentRequest,
    SearchResult,
    SummarizeDocumentRequest,
    SummaryType,
)
from apps.document_qa.qa import DocumentQAAssistant
from apps.document_qa.summarizer import DocumentSummarizer

logger = logging.getLogger("JARVIS.API.DocumentQA")

document_qa_router = APIRouter(prefix="/document-qa", tags=["document-qa"])

_qa_assistant = DocumentQAAssistant(index=document_index, database=doc_db)
_summarizer = DocumentSummarizer(database=doc_db)

STORAGE_ROOT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data",
    "documents",
)
os.makedirs(STORAGE_ROOT, exist_ok=True)


def get_current_user_identity() -> AppRequestIdentity:
    """Resolve requesting user identity and role."""
    try:
        return apps_permissions.get_current_identity()
    except Exception:
        return AppRequestIdentity(user_id="default_user", display_name="User", role=UserRole.USER)


def require_non_guest(identity: AppRequestIdentity) -> None:
    role_val = identity.role.value if hasattr(identity.role, "value") else str(identity.role).upper()
    if role_val == "GUEST":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="GUEST role cannot upload or delete documents. Elevated privileges required.",
        )


# On startup, warm up document index with stored chunks
try:
    existing_chunks = doc_db.load_all_chunks()
    if existing_chunks:
        document_index.add_chunks(existing_chunks)
        logger.info("Warmed up Document AI index with %d chunks", len(existing_chunks))
except Exception as ex:
    logger.warning("Could not pre-warm document index: %s", ex)


@document_qa_router.get("/status")
def get_document_qa_status(identity: AppRequestIdentity = Depends(get_current_user_identity)):
    """Health check and telemetry for Document AI."""
    docs = doc_db.list_documents(identity.user_id)
    return {
        "status": "ready",
        "app_id": "document-qa",
        "display_name": "Document Question Answering",
        "user_id": identity.user_id,
        "role": identity.role.value if hasattr(identity.role, "value") else str(identity.role),
        "total_user_documents": len(docs),
        "total_indexed_chunks": len(document_index._chunks),
        "supported_formats": ["pdf", "docx", "txt", "md", "csv"],
        "rag_engine": "hybrid_tfidf_cosine_bm25",
    }


@document_qa_router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    collection: str = Form("default"),
    title: Optional[str] = Form(None),
    author: Optional[str] = Form(None),
    identity: AppRequestIdentity = Depends(get_current_user_identity),
):
    """Upload and process a document into the RAG pipeline."""
    require_non_guest(identity)

    safe_name = sanitize_filename(file.filename or "uploaded_file")
    user_dir = os.path.join(STORAGE_ROOT, identity.user_id)
    os.makedirs(user_dir, exist_ok=True)

    doc_id = f"doc_{uuid.uuid4().hex[:12]}"
    target_path = os.path.join(user_dir, f"{doc_id}_{safe_name}")

    # Stream file to disk
    try:
        with open(target_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        logger.error("Failed writing uploaded file to %s: %s", target_path, e)
        raise HTTPException(status_code=500, detail=f"Failed storing uploaded document: {e}")

    try:
        # Extract text and structural pages
        extracted = extractor.extract(target_path, original_filename=safe_name)

        # Chunk document
        chunks = chunk_document(extracted, doc_id=doc_id, user_id=identity.user_id)

        meta = DocumentMetadata(
            doc_id=doc_id,
            filename=safe_name,
            file_type=extracted.file_type,
            file_size_bytes=extracted.file_size_bytes,
            user_id=identity.user_id,
            page_count=extracted.total_pages,
            word_count=extracted.total_words,
            checksum=extracted.checksum,
            collection=collection.strip() or "default",
            is_indexed=True,
            storage_path=target_path,
            title=title or extracted.title,
            author=author or extracted.author,
            metadata_json=extracted.metadata_json,
        )

        # Persist to database
        doc_db.save_document(meta)
        doc_db.save_chunks(chunks)

        # Index in search engine
        document_index.add_chunks(chunks)

        logger.info("Successfully ingested document '%s' (ID: %s, Chunks: %d)", safe_name, doc_id, len(chunks))
        return {
            "status": "ok",
            "message": f"Document '{safe_name}' uploaded and indexed successfully.",
            "document": meta.model_dump(),
            "chunks_count": len(chunks),
        }
    except Exception as ex:
        # Cleanup file if processing failed
        if os.path.exists(target_path):
            os.unlink(target_path)
        logger.error("Document ingestion failed: %s", ex)
        raise HTTPException(status_code=400, detail=f"Document processing failed: {str(ex)}")


@document_qa_router.get("/documents")
def list_documents(
    collection: Optional[str] = Query(None),
    identity: AppRequestIdentity = Depends(get_current_user_identity),
):
    """List documents belonging to requesting user."""
    docs = doc_db.list_documents(identity.user_id, collection=collection)
    return {"status": "ok", "documents": [d.model_dump() for d in docs]}


@document_qa_router.get("/documents/{doc_id}")
def get_document_details(
    doc_id: str,
    identity: AppRequestIdentity = Depends(get_current_user_identity),
):
    """Retrieve document metadata and chunk index."""
    meta = doc_db.get_document(doc_id, identity.user_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Document not found or access denied.")

    chunks = doc_db.get_document_chunks(doc_id, identity.user_id)
    return {
        "status": "ok",
        "document": meta.model_dump(),
        "chunks": [c.model_dump() for c in chunks],
    }


@document_qa_router.delete("/documents/{doc_id}")
def delete_document(
    doc_id: str,
    identity: AppRequestIdentity = Depends(get_current_user_identity),
):
    """Delete a document and purge all chunks from search index and filesystem."""
    require_non_guest(identity)
    path = doc_db.delete_document(doc_id, identity.user_id)
    if not path:
        raise HTTPException(status_code=404, detail="Document not found or access denied.")

    # Remove from search index
    document_index.remove_document(doc_id)

    # Delete file from storage
    if os.path.exists(path):
        try:
            os.unlink(path)
        except Exception as ex:
            logger.warning("Could not delete physical document %s: %s", path, ex)

    return {"status": "ok", "message": f"Document '{doc_id}' deleted successfully."}


@document_qa_router.post("/search")
def search_documents(
    req: SearchDocumentRequest,
    identity: AppRequestIdentity = Depends(get_current_user_identity),
):
    """Perform hybrid semantic and keyword search across user documents."""
    results = document_index.search(
        query=req.query,
        user_id=identity.user_id,
        doc_ids=req.doc_ids,
        top_k=req.top_k,
    )
    return {
        "status": "ok",
        "query": req.query,
        "results_count": len(results),
        "results": [r.model_dump() for r in results],
    }


@document_qa_router.post("/ask")
def ask_question(
    req: AskDocumentRequest,
    identity: AppRequestIdentity = Depends(get_current_user_identity),
):
    """Ask a question and receive a grounded answer with verified citations."""
    target_docs = req.doc_ids
    if not target_docs and (req.doc_id or req.document_id):
        target_docs = [req.doc_id or req.document_id]

    answer = _qa_assistant.ask(
        question=req.question,
        user_id=identity.user_id,
        doc_ids=target_docs,
        top_k=req.top_k,
        provider=req.provider,
    )
    return {"status": "ok", "answer": answer.model_dump()}


@document_qa_router.post("/summarize")
def summarize_document(
    req: SummarizeDocumentRequest,
    identity: AppRequestIdentity = Depends(get_current_user_identity),
):
    """Generate a structured summary for a document."""
    try:
        summary = _summarizer.summarize(
            doc_id=req.doc_id,
            user_id=identity.user_id,
            summary_type=req.summary_type,
            provider=req.provider,
        )
        return {"status": "ok", "summary": summary.model_dump()}
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))


@document_qa_router.get("/collections")
def list_collections(identity: AppRequestIdentity = Depends(get_current_user_identity)):
    """List document collections for user."""
    collections = doc_db.list_collections(identity.user_id)
    return {"status": "ok", "collections": [c.model_dump() for c in collections]}


@document_qa_router.post("/collections", status_code=status.HTTP_201_CREATED)
def create_collection(
    req: CreateCollectionRequest,
    identity: AppRequestIdentity = Depends(get_current_user_identity),
):
    """Create a new collection for user."""
    require_non_guest(identity)
    col = doc_db.create_collection(identity.user_id, req.name, req.description or "")
    return {"status": "ok", "collection": col.model_dump()}
