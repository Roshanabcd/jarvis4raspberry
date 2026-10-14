from fastapi import APIRouter
from memory.long_term.database import db
from pydantic import BaseModel

memory_router = APIRouter(prefix="/memory")

class MemoryStoreRequest(BaseModel):
    category: str
    content: str

@memory_router.post("/store")
def store_memory(req: MemoryStoreRequest):
    db.store(req.category, req.content)
    return {"status": "stored"}

@memory_router.get("/search")
def search_memory(category: str = None):
    results = db.search(category)
    return {"status": "ok", "data": results}
