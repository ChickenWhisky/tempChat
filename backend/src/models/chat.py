from pydantic import BaseModel
from typing import Literal


from pydantic_ai.messages import ModelMessage


# Incoming request model
class ChatRequest(BaseModel):
    message: str
    message_id: str | None = None
    history: list[ModelMessage] | None = None


# Outgoing SSE Event models
class StartEvent(BaseModel):
    type: Literal["start"] = "start"
    message_id: str


class TokenEvent(BaseModel):
    type: Literal["token"] = "token"
    message_id: str
    content: str


class EndEvent(BaseModel):
    type: Literal["end"] = "end"
    message_id: str


class ErrorEvent(BaseModel):
    type: Literal["error"] = "error"
    message_id: str
    error: str
