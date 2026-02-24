from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from src.models.chat import ChatRequest
from src.services.llm_agent import stream_llm_response

router = APIRouter()

@router.post("/chat", summary="Stream a chat response")
async def chat_stream(request: ChatRequest):
    """
    Streams the response back to the client using Server-Sent Events (SSE).
    """
    # Use FastAPI's StreamingResponse with the correct media type for SSE
    return StreamingResponse(
        stream_llm_response(request.message),
        media_type="text/event-stream"
    )
