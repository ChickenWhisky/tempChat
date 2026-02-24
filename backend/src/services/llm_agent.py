from dataclasses import dataclass
from typing import AsyncIterable, Any

from pydantic_ai import Agent, RunContext
from pydantic_ai.durable_exec.temporal import TemporalAgent
from pydantic_ai.messages import ModelMessage, ModelResponse, TextPart
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.ollama import OllamaProvider

from src.core.config import settings
from src.core.pubsub import pubsub_manager
from src.models.chat import TokenEvent

ollama_model = OpenAIChatModel(
    model_name=settings.OLLAMA_MODEL,
    provider=OllamaProvider(base_url=settings.OLLAMA_BASE_URL),
)


@dataclass
class ChatDeps:
    message_id: str
    message_history: list[ModelMessage] | None = None


async def my_event_stream_handler(
    ctx: RunContext[ChatDeps], events: AsyncIterable[Any]
) -> None:
    """
    This handler runs in a standard Temporal Activity (spawned by TemporalAgent).
    It receives the stream of parts and publishes them to our in-memory queue.
    """
    channel = ctx.deps.message_id

    async for event in events:
        # Pydantic AI streams ModelResponse events containing parts
        if isinstance(event, ModelResponse):
            for part in event.parts:
                if isinstance(part, TextPart):
                    token_event = TokenEvent(message_id=channel, content=part.content)
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
