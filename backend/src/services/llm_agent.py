from dataclasses import dataclass
from typing import AsyncIterable, Any

from pydantic_ai import Agent, RunContext
from pydantic_ai.durable_exec.temporal import TemporalAgent
from pydantic_ai.messages import ModelMessage
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.ollama import OllamaProvider

from src.core.config import settings
from src.core.pubsub import pubsub_manager
from src.models.chat import StreamEvent
import logging
from temporalio.workflow import ActivityConfig
from datetime import timedelta

ollama_model = OpenAIChatModel(
    model_name=settings.OLLAMA_MODEL,
    provider=OllamaProvider(base_url=settings.OLLAMA_BASE_URL),
)


@dataclass
class ChatDeps:
    message_id: str
    message_history: list[ModelMessage] | None = None


logger = logging.getLogger(__name__)


async def _publish_token(channel: str, content: str | None):
    if content:
        event = StreamEvent(type="token", message_id=channel, content=str(content))
        await pubsub_manager.publish(channel, f"data: {event.model_dump_json()}\n\n")


async def my_event_stream_handler(
    ctx: RunContext[ChatDeps], events: AsyncIterable[Any]
) -> None:
    """
    This handler runs in a standard Temporal Activity (spawned by TemporalAgent).
    It receives the stream of parts and publishes them to our in-memory queue.
    """
    channel = ctx.deps.message_id
    logger.info(f"[{channel}] Started AI response stream")

    async for event in events:
        event_name = type(event).__name__

        # 1. Handle PartStartEvent (May contain initial content for some providers)
        if event_name == "PartStartEvent":
            part = getattr(event, "part", None)
            if part:
                content = getattr(part, "content", None) or getattr(part, "text", None)
                await _publish_token(channel, content)

        # 2. Handle PartDeltaEvent (Common for streaming)
        elif event_name == "PartDeltaEvent":
            delta = getattr(event, "delta", None)
            content = None
            if delta is not None:
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

            await _publish_token(channel, content)

        # 3. Handle ModelResponse (Check parts)
        elif hasattr(event, "parts"):
            for part in getattr(event, "parts", []):
                content = getattr(part, "content", None) or getattr(part, "text", None)
                await _publish_token(channel, content)

        # 4. Last resort content check on the event itself
        elif hasattr(event, "content") and isinstance(
            getattr(event, "content", None), str
        ):
            await _publish_token(channel, getattr(event, "content"))

    # 5. Signal the end of the stream for this turn
    end_event = StreamEvent(type="end", message_id=channel)
    await pubsub_manager.publish(channel, f"data: {end_event.model_dump_json()}\n\n")
    logger.info(f"[{channel}] Finished AI response stream")


# Upgrade the agent to expect ChatDeps
agent = Agent(
    model=ollama_model,
    deps_type=ChatDeps,
    system_prompt="You are a helpful AI assistant. Provide concise and accurate answers.",
)

# Export the TemporalAgent
temporal_agent = TemporalAgent(
    agent,
    name="chat_agent",
    event_stream_handler=my_event_stream_handler,
    activity_config=ActivityConfig(start_to_close_timeout=timedelta(minutes=2)),
)
