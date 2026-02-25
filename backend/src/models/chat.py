from pydantic import BaseModel
from typing import Literal


# Incoming request model
class ChatRequest(BaseModel):
    message: str
    conversation_id: str
    message_id: str | None = None


# Outgoing SSE Event model
class StreamEvent(BaseModel):
    type: Literal["start", "token", "end", "error"]
    message_id: str
    content: str | None = None
    error: str | None = None
