from dataclasses import dataclass
from typing import AsyncIterable, Any

from pydantic_ai import Agent, RunContext
from pydantic_ai.durable_exec.temporal import TemporalAgent
from pydantic_ai.messages import ModelMessage
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.ollama import OllamaProvider

from src.core.config import settings
from src.core.pubsub import pubsub_manager
from src.models.chat import TokenEvent
import logging

ollama_model = OpenAIChatModel(
    model_name=settings.OLLAMA_MODEL,
    provider=OllamaProvider(base_url=settings.OLLAMA_BASE_URL),
)


@dataclass
class ChatDeps:
    message_id: str
    message_history: list[ModelMessage] | None = None


logger = logging.getLogger(__name__)


async def my_event_stream_handler(
    ctx: RunContext[ChatDeps], events: AsyncIterable[Any]
) -> None:
    """
    This handler runs in a standard Temporal Activity (spawned by TemporalAgent).
    It receives the stream of parts and publishes them to our in-memory queue.
    """
    logger.warning(f"DEBUG: STARTING STREAM HANDLER for {ctx.deps.message_id}")
    channel = ctx.deps.message_id

    async for event in events:
        # Pydantic AI streams ModelResponse events containing parts
        # For actual streaming, it yields PartDeltaEvent
        # We handle any event that has text content or deltas.
        if event.__class__.__name__ == "PartDeltaEvent":
            delta = getattr(event, "delta", None)
            logger.warning(
                f"DEBUG llm_agent: Received delta: {delta} of type {type(delta)}"
            )

            # Use string representation if we don't know the field, but try to find it
            content = None
            if hasattr(delta, "content_chunk"):
                content = delta.content_chunk
            elif hasattr(delta, "content_delta"):
                content = delta.content_delta
            elif hasattr(delta, "text"):
                content = delta.text
            elif hasattr(delta, "content"):
                content = delta.content

            if content is None:
                # Last resort fallback: maybe delta itself is the string?
                if isinstance(delta, str):
                    content = delta
                else:
                    # Let's inspect the fields with logger
                    logger.warning(f"DEBUG llm_agent: delta dir: {dir(delta)}")

            if content:
                token_event = TokenEvent(message_id=channel, content=str(content))
                await pubsub_manager.publish(
                    channel, f"data: {token_event.model_dump_json()}\n\n"
                )
        elif hasattr(event, "parts"):
            for part in getattr(event, "parts", []):
                content = getattr(part, "content", None)
                if content:
                    token_event = TokenEvent(message_id=channel, content=content)
                    await pubsub_manager.publish(
                        channel, f"data: {token_event.model_dump_json()}\n\n"
                    )
        elif hasattr(event, "content") and isinstance(
            getattr(event, "content", None), str
        ):
            content = getattr(event, "content")
            token_event = TokenEvent(message_id=channel, content=content)
            await pubsub_manager.publish(
                channel, f"data: {token_event.model_dump_json()}\n\n"
            )


# Upgrade the agent to expect ChatDeps
agent = Agent(
    model=ollama_model,
    deps_type=ChatDeps,
    system_prompt="You are a helpful AI assistant. Provide concise and accurate answers.",
)

# Export the TemporalAgent
temporal_agent = TemporalAgent(
    agent, name="chat_agent", event_stream_handler=my_event_stream_handler
)
