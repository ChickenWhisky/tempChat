from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
from temporalio.worker import Worker
from src.core.config import settings
from src.core.temporal import TemporalClient
from src.api.routes import stream
from src.workflows.chat import ChatWorkflow


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Connect to Temporal on startup
    client = await TemporalClient.get_client()

    # Run a Temporal Worker directly inside the FastAPI app
    # This avoids the need for a separate `backend-worker` container for now.
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


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# Set all CORS enabled origins
if settings.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Include routers
app.include_router(stream.router, prefix=settings.API_V1_STR, tags=["chat"])


@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok"}
