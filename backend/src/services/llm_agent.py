from dataclasses import dataclass
from typing import AsyncIterable, Any

from pydantic_ai import Agent, RunContext
from pydantic_ai.durable_exec.temporal import TemporalAgent
from pydantic_ai.messages import ModelMessage
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.ollama import OllamaProvider

from src.core.config import settings
from src.core.pubsub import pubsub_manager
from src.models.chat import TokenEvent, EndEvent
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
    channel = ctx.deps.message_id
    logger.warning(f"DEBUG llm_agent [{channel}]: STARTING STREAM HANDLER")

    async for event in events:
        event_name = type(event).__name__
        logger.warning(
            f"DEBUG llm_agent [{channel}]: Received event type: {event_name}"
        )

        # 1. Handle PartStartEvent (May contain initial content for some providers)
        if event_name == "PartStartEvent":
            part = getattr(event, "part", None)
            if part:
                logger.warning(
                    f"DEBUG llm_agent [{channel}]: PartStart part type: {type(part).__name__}"
                )
                content = None
                if hasattr(part, "content"):
                    content = part.content
                elif hasattr(part, "text"):
                    content = part.text

                if content:
                    logger.warning(
                        f"DEBUG llm_agent [{channel}]: Found content in PartStart: {str(content)[:20]}..."
                    )
                    token_event = TokenEvent(message_id=channel, content=str(content))
                    await pubsub_manager.publish(
                        channel, f"data: {token_event.model_dump_json()}\n\n"
                    )

        # 2. Handle PartDeltaEvent (Common for streaming)
        elif event_name == "PartDeltaEvent":
            delta = getattr(event, "delta", None)
            content = None
            if hasattr(delta, "content_chunk"):
                content = delta.content_chunk
            elif hasattr(delta, "content_delta"):
                content = delta.content_delta
            elif hasattr(delta, "text"):
                content = delta.text
            elif hasattr(delta, "content"):
                content = delta.content
            elif isinstance(delta, str):
                content = delta

            if content:
                logger.warning(
                    f"DEBUG llm_agent [{channel}]: Found token in Delta: {str(content)[:20]}..."
                )
                token_event = TokenEvent(message_id=channel, content=str(content))
                await pubsub_manager.publish(
                    channel, f"data: {token_event.model_dump_json()}\n\n"
                )

        # 3. Handle ModelResponse (Check parts)
        elif hasattr(event, "parts"):
            parts = getattr(event, "parts", [])
            for i, part in enumerate(parts):
                content = getattr(part, "content", None) or getattr(part, "text", None)
                if content:
                    logger.warning(
                        f"DEBUG llm_agent [{channel}]: Found content in ModelResponse part {i}: {str(content)[:20]}..."
                    )
                    token_event = TokenEvent(message_id=channel, content=str(content))
                    await pubsub_manager.publish(
                        channel, f"data: {token_event.model_dump_json()}\n\n"
                    )

        # 4. Last resort content check on the event itself
        elif hasattr(event, "content") and isinstance(
            getattr(event, "content", None), str
        ):
            content = getattr(event, "content")
            if content:
                logger.warning(
                    f"DEBUG llm_agent [{channel}]: Found token in event attr: {str(content)[:20]}..."
                )
                token_event = TokenEvent(message_id=channel, content=content)
                await pubsub_manager.publish(
                    channel, f"data: {token_event.model_dump_json()}\n\n"
                )

    # 5. Signal the end of the stream for this turn

    end_event = EndEvent(message_id=channel)
    await pubsub_manager.publish(channel, f"data: {end_event.model_dump_json()}\n\n")


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
