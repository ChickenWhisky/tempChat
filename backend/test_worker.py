import asyncio
from temporalio.client import Client
from temporalio.worker import Worker
from src.workflows.chat import ChatWorkflow
from src.services.llm_agent import temporal_agent
from src.core.config import settings
import traceback
from pydantic_ai.durable_exec.temporal import PydanticAIPlugin


async def test():
    try:
        client = await Client.connect("localhost:7233", plugins=[PydanticAIPlugin()])
        print("Connected to Temporal.")
        worker = Worker(
            client,
            task_queue=settings.TEMPORAL_TASK_QUEUE,
            workflows=[ChatWorkflow],
            activities=temporal_agent.temporal_activities,
        )
        print("Worker initialized.")
    except Exception as e:
        print("EXCEPTION CAUSE:")
        if e.__cause__:
            traceback.print_exception(
                type(e.__cause__), e.__cause__, e.__cause__.__traceback__
            )
        else:
            traceback.print_exception(type(e), e, e.__traceback__)


if __name__ == "__main__":
    asyncio.run(test())
