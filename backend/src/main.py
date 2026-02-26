from fastapi import FastAPI
from contextlib import asynccontextmanager
import asyncio
from temporalio.worker import Worker
from src.core.config import settings
from src.core.temporal import TemporalClient
from src.api.routes import stream, history
from src.workflows.chat import ChatWorkflow
from src.core.pubsub import pubsub_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles application startup and shutdown events, connecting to Temporal/Redis
    and running the background worker.
    """
    # Connect to Temporal and Redis on startup
    await pubsub_manager.connect()
    client = await TemporalClient.get_client()

    # Run a Temporal Worker directly inside the FastAPI app
    worker = Worker(
        client,
        task_queue=settings.TEMPORAL_TASK_QUEUE,
        workflows=[ChatWorkflow],
    )

    # Run the worker concurrently in the background
    worker_task = asyncio.create_task(worker.run())

    yield

    # Shut down cleanly
    worker_task.cancel()
    try:
        await worker_task
    except asyncio.CancelledError:
        pass
    await TemporalClient.close_client()
    await pubsub_manager.disconnect()


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# Include routers
app.include_router(stream.router, prefix=settings.API_V1_STR, tags=["chat"])
app.include_router(
    history.router, prefix=f"{settings.API_V1_STR}/chat", tags=["chat_history"]
)


@app.get("/health", tags=["health"])
def health_check():
    """
    Simple health check endpoint to verify the service is running.
    """
    return {"status": "ok"}
