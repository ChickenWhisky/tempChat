from pydantic_ai.providers.ollama import OllamaProvider
from pydantic_ai.models.openai import OpenAIChatModel
import asyncio
import uuid
import json
from openai import AsyncOpenAI
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIModel
from src.models.chat import StartEvent, TokenEvent, EndEvent, ErrorEvent
from src.core.config import settings



ollama_model = OpenAIChatModel(
    model_name=settings.OLLAMA_MODEL,
    provider=OllamaProvider(base_url=settings.OLLAMA_BASE_URL) 

)

# Define the PydanticAI agent
agent = Agent(
    model=ollama_model,
    system_prompt="You are a helpful AI assistant. Provide concise and accurate answers."
)

async def stream_llm_response(prompt: str):
    """
    Streams the LLM response back to the client using Server-Sent Events (SSE).
    Uses PydanticAI's streaming interface.
    """
    msg_id = str(uuid.uuid4())

    # 1. Send start event
    start_event = StartEvent(message_id=msg_id)
    yield f"data: {start_event.model_dump_json()}\n\n"

    try:
        # 2. Open a streaming run with the agent
        async with agent.run_stream(prompt) as result:
            # 3. Stream tokens
            async for data in result.stream_text(delta=True):
                # We yield the individual chunks (deltas) directly.
                # OpenAI model streams text chunks.
                token_event = TokenEvent(message_id=msg_id, content=data)
                yield f"data: {token_event.model_dump_json()}\n\n"

        # 4. Send end event upon complete generation
        end_event = EndEvent(message_id=msg_id)
        yield f"data: {end_event.model_dump_json()}\n\n"
        
    except Exception as e:
        # 5. Send error event on failure
        error_event = ErrorEvent(message_id=msg_id, error=str(e))
        yield f"data: {error_event.model_dump_json()}\n\n"
