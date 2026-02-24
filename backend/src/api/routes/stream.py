from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from ..models.chat import ChatRequest
from ..services.fake_generator import generate_fake_tokens

router = APIRouter()

@router.post("/chat", summary="Stream a chat response")
async def chat_stream(request: ChatRequest):
    """
    Streams the response back to the client using Server-Sent Events (SSE).
    """
    # Use FastAPI's StreamingResponse with the correct media type for SSE
    return StreamingResponse(
        generate_fake_tokens(request.message),
        media_type="text/event-stream"
    )
