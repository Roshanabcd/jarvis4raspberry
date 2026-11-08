from typing import Optional
from fastapi import APIRouter, HTTPException
from memory.long_term.database import db
from pydantic import BaseModel, Field

memory_router = APIRouter(prefix="/memory", tags=["memory"])


class MemoryStoreRequest(BaseModel):
    category: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)
    importance: Optional[int] = 5


@memory_router.post("/store")
def store_memory(req: MemoryStoreRequest):
    row_id = db.store(category=req.category, content=req.content, importance=req.importance or 5)
    return {"status": "stored", "id": row_id}


@memory_router.get("/search")
def search_memory(query: str = "", category: Optional[str] = None, limit: int = 50):
    results = db.search(query=query, category=category, limit=limit)
    return {"status": "ok", "data": results, "total": len(results)}


@memory_router.delete("/{memory_id}")
def delete_memory(memory_id: int):
    ok = db.delete(memory_id)
    return {"status": "ok", "deleted": ok, "id": memory_id}


@memory_router.get("/categories")
def get_categories():
    return {
        "status": "ok",
        "categories": sorted(list(getattr(db, "VALID_CATEGORIES", ["USER", "PROJECT", "ROBOT", "SYSTEM", "CONVERSATION", "TASK", "KNOWLEDGE", "PREFERENCE", "EVENT"])))
    }


@memory_router.get("/stats")
def memory_stats():
    return db.summarize()
