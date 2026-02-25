from temporalio.client import Client
from src.core.config import settings
from pydantic_ai.durable_exec.temporal import PydanticAIPlugin


# Global client registry for the FastAPI app
class TemporalClient:
    _client: Client | None = None

    @classmethod
    async def get_client(cls) -> Client:
        if cls._client is None:
            # Connect to Temporal server

            cls._client = await Client.connect(
                settings.TEMPORAL_HOST, plugins=[PydanticAIPlugin()]
            )
        return cls._client

    @classmethod
    async def close_client(cls):
        cls._client = None
