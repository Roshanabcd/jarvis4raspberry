from fastapi import APIRouter
from apps.voice.service import voice_service
from pydantic import BaseModel

voice_router = APIRouter(prefix="/voice")

class CommandRequest(BaseModel):
    text: str

@voice_router.post("/command")
def run_command(req: CommandRequest):
    response = voice_service.process_command(req.text)
    return {"status": "ok", "response": response}
