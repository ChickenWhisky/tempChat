import logging
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import uuid
from src.models.chat import ChatRequest, StreamEvent
from src.core.temporal import TemporalClient
from src.core.config import settings
from src.workflows.chat import ChatWorkflow
from src.core.pubsub import pubsub_manager
from temporalio.exceptions import WorkflowAlreadyStartedError

logger = logging.getLogger(__name__)

router = APIRouter()


async def handle_chat_stream(
    message: str,
    conversation_id: str,
    message_id: str | None = None,
):
    """
    Spawns/Signals the durable Temporal workflow and then simulates the SSE streaming
    format the frontend expects by listening to the PubSub queue.
    """
    msg_id = message_id or str(uuid.uuid4())
    pubsub = await pubsub_manager.subscribe(msg_id)

    start_event = StreamEvent(type="start", message_id=msg_id)
    yield f"data: {start_event.model_dump_json()}\n\n"

    try:
        client = await TemporalClient.get_client()

        # Start or signal the workflow durably
        workflow_id = f"chat-{conversation_id}"

        try:
            await client.start_workflow(
                ChatWorkflow.run,
                id=workflow_id,
                task_queue=settings.TEMPORAL_TASK_QUEUE,
                start_signal="post_message",
                start_signal_args=[message, msg_id],
            )
        except WorkflowAlreadyStartedError:
            handle = client.get_workflow_handle(workflow_id)
            await handle.signal(ChatWorkflow.post_message, message, msg_id)  # type: ignore

        # Stream responses from the pubsub
        async for message in pubsub.listen():
            if isinstance(message, dict) and message.get("type") == "message":
                chunk = message.get("data")
                if isinstance(chunk, str):
                    yield chunk

                    # A turn is finished when we see an 'end' event in the stream
                    if '"type":"end"' in chunk or '"type": "end"' in chunk:
                        break

    except Exception as e:
        logger.error(f"Exception in stream for {msg_id}: {e}")
        error_event = StreamEvent(type="error", message_id=msg_id, error=str(e))
        yield f"data: {error_event.model_dump_json()}\n\n"
    finally:
        await pubsub.unsubscribe(msg_id)


@router.post("/chat", summary="Stream a chat response")
async def chat_stream(request: ChatRequest):
    """
    Executes a durable Temporal Workflow but returns the
    response using Server-Sent Events (SSE) formatting.
    """
    return StreamingResponse(
        handle_chat_stream(
            request.message,
            request.conversation_id,
            request.message_id,
        ),
        media_type="text/event-stream",
    )
