from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import asyncio
import uuid
from src.models.chat import ChatRequest, StartEvent, EndEvent, ErrorEvent
from src.core.temporal import TemporalClient
from src.core.config import settings
from src.workflows.chat import ChatWorkflow
from src.core.pubsub import pubsub_manager

router = APIRouter()


async def simulate_streaming_response(message: str):
    """
    Spawns the durable Temporal workflow and then simulates the SSE streaming
    format the frontend expects by listening to the PubSub queue.
    """
    msg_id = str(uuid.uuid4())
    queue = pubsub_manager.subscribe(msg_id)

    # 1. Send start event
    start_event = StartEvent(message_id=msg_id)
    yield f"data: {start_event.model_dump_json()}\n\n"

    try:
        client = await TemporalClient.get_client()

        # Start the workflow durably (in the background)
        workflow_handle = await client.start_workflow(
            ChatWorkflow.run,
            args=[message, msg_id, None],  # prompt, message_id, message_history
            id=f"chat-{msg_id}",
            task_queue=settings.TEMPORAL_TASK_QUEUE,
        )

        # Stream responses from the queue until the workflow completes
        workflow_task = asyncio.create_task(workflow_handle.result())

        while True:
            # Wait for either a new SSE chunk or the workflow to finish
            get_task = asyncio.create_task(queue.get())
            done, pending = await asyncio.wait(
                [get_task, workflow_task], return_when=asyncio.FIRST_COMPLETED
            )

            if get_task in done:
                chunk = get_task.result()
                yield chunk
            else:
                get_task.cancel()
                # Empty remaining queue
                while not queue.empty():
                    yield queue.get_nowait()
                break

            if workflow_task in done:
                get_task.cancel()
                while not queue.empty():
                    yield queue.get_nowait()
                break

        # Wait for actual result to ensure any workflow exceptions bubble up
        await workflow_task

        # Send end event
        end_event = EndEvent(message_id=msg_id)
        yield f"data: {end_event.model_dump_json()}\n\n"

    except Exception as e:
        error_event = ErrorEvent(message_id=msg_id, error=str(e))
        yield f"data: {error_event.model_dump_json()}\n\n"
    finally:
        pubsub_manager.unsubscribe(msg_id, queue)


@router.post("/chat", summary="Stream a chat response")
async def chat_stream(request: ChatRequest):
    """
    Executes a durable Temporal Workflow but returns the
    response using Server-Sent Events (SSE) formatting.
    """
    return StreamingResponse(
        simulate_streaming_response(request.message), media_type="text/event-stream"
    )
