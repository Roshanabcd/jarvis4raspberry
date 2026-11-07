from typing import Optional
from fastapi import APIRouter
from memory.long_term.database import db
from pydantic import BaseModel

memory_router = APIRouter(prefix="/memory")

class MemoryStoreRequest(BaseModel):
    category: str
    content: str

@memory_router.post("/store")
def store_memory(req: MemoryStoreRequest):
    row_id = db.store(req.category, req.content)
    return {"status": "stored", "id": row_id}

@memory_router.get("/search")
def search_memory(query: str = "", category: Optional[str] = None, limit: int = 20):
    results = db.search(query=query, category=category, limit=limit)
    return {"status": "ok", "data": results}
