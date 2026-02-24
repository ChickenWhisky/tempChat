import asyncio
from typing import Dict, List


class PubSubManager:
    """
    A simple in-memory Publisher/Subscriber to bridge Temporal Activities (running in the same process)
    with the FastAPI SSE endpoints.

    In a multi-worker production environment, this should be replaced by Redis PubSub.
    """

    def __init__(self):
        self._channels: Dict[str, List[asyncio.Queue[str]]] = {}

    def subscribe(self, channel: str) -> asyncio.Queue[str]:
        if channel not in self._channels:
            self._channels[channel] = []
        queue = asyncio.Queue()
        self._channels[channel].append(queue)
        return queue

    def unsubscribe(self, channel: str, queue: asyncio.Queue[str]):
        if channel in self._channels:
            if queue in self._channels[channel]:
                self._channels[channel].remove(queue)
            if not self._channels[channel]:
                del self._channels[channel]

    async def publish(self, channel: str, message: str):
        if channel in self._channels:
            for queue in self._channels[channel]:
                await queue.put(message)


# Global singleton
pubsub_manager = PubSubManager()
