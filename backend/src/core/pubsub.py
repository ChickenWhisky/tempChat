from redis.asyncio.client import PubSub
import redis.asyncio as redis
from src.core.config import settings
import logging

logger = logging.getLogger(__name__)


class PubSubManager:
    """
    A Redis-backed Publisher/Subscriber to bridge Temporal Activities (running on different workers/threads)
    with the FastAPI SSE endpoints.
    """

    def __init__(self):
        self._redis: redis.Redis | None = None

    async def connect(self):
        self._redis = redis.from_url(settings.REDIS_URL, decode_responses=True)
        logger.info(f"Connected to Redis PubSub at {settings.REDIS_URL}")

    async def disconnect(self):
        if self._redis:
            await self._redis.aclose()
            logger.info("Disconnected from Redis PubSub")

    async def subscribe(self, channel: str) -> PubSub:
        if not self._redis:
            raise RuntimeError("Redis client is not connected")

        pubsub = self._redis.pubsub()
        await pubsub.subscribe(channel)
        logger.info(f"Subscribed to Redis channel: {channel}")
        return pubsub

    async def publish(self, channel: str, message: str):
        if not self._redis:
            logger.error("Publish failed: Redis client is not connected")
            return

        await self._redis.publish(channel, message)


# Global singleton
pubsub_manager = PubSubManager()
