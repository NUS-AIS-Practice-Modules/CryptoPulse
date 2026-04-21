import uuid
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from src.services.chat_service import handle_chat

router = APIRouter()


class ChatOptions(BaseModel):
    include_sentiment: bool = True
    include_sources: bool = True


class ChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None
    options: ChatOptions = ChatOptions()


@router.post("/api/chat")
async def chat(request: ChatRequest):
    if not request.message.strip():
        raise HTTPException(status_code=422, detail="message cannot be empty")

    conv_id = request.conversation_id or str(uuid.uuid4())

    try:
        result = await handle_chat(
            message=request.message,
            conversation_id=conv_id,
            include_sentiment=request.options.include_sentiment,
            include_sources=request.options.include_sources,
        )
        return result
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=f"Upstream unavailable: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {e}")
