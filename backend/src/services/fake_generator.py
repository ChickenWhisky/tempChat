import asyncio
import uuid
import json
from src.models.chat import StartEvent, TokenEvent, EndEvent, ErrorEvent

async def generate_fake_tokens(prompt: str):
    """
    Simulates a streaming response yielding JSON strings formatted as Server-Sent Events.
    Must follow the strict Streaming Protocol Specification.

    Wire format:
    data: <json>\n\n
    """
    msg_id = str(uuid.uuid4())

    # 1. Send start event
    start_event = StartEvent(message_id=msg_id)
    yield f"data: {start_event.model_dump_json()}\n\n"

    try:
        # Simulate processing delay
        await asyncio.sleep(0.5)

        # 2. Stream tokens
        fake_response = f"This is a fake streamed response to: '{prompt}'."
        words = fake_response.split(" ")
        
        for i, word in enumerate(words):
            # add space back except for first word
            content = word if i == 0 else f" {word}"
            token_event = TokenEvent(message_id=msg_id, content=content)
            yield f"data: {token_event.model_dump_json()}\n\n"
            await asyncio.sleep(0.1) # Simulate token generation delay

        # 3. Send end event
        end_event = EndEvent(message_id=msg_id)
        yield f"data: {end_event.model_dump_json()}\n\n"
        
    except Exception as e:
        # Send error event on failure
        error_event = ErrorEvent(message_id=msg_id, error=str(e))
        yield f"data: {error_event.model_dump_json()}\n\n"
