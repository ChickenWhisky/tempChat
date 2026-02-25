from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import uuid
from src.models.chat import ChatRequest, StartEvent, ErrorEvent
from src.core.temporal import TemporalClient
from src.core.config import settings
from src.workflows.chat import ChatWorkflow
from src.core.pubsub import pubsub_manager
from temporalio.exceptions import WorkflowAlreadyStartedError

router = APIRouter()


async def simulate_streaming_response(
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

    # 1. Send start event
    start_event = StartEvent(message_id=msg_id)
    yield f"data: {start_event.model_dump_json()}\n\n"

    try:
        client = await TemporalClient.get_client()

        # Start or signal the workflow durably
        workflow_id = f"chat-{conversation_id}"
        # Signal-With-Start: Starts the workflow if not running, AND signals it in one go.
        workflow_id = f"chat-{conversation_id}"
        print(f"DEBUG stream.py: Signal-With-Start for {workflow_id}")

        try:
            await client.start_workflow(
                ChatWorkflow.run,
                id=workflow_id,
                task_queue=settings.TEMPORAL_TASK_QUEUE,
                start_signal="post_message",
                start_signal_args=[message, msg_id],
            )
        except WorkflowAlreadyStartedError:
            print(
                f"DEBUG stream.py: Workflow already running, signaling existing workflow {workflow_id}"
            )
            handle = client.get_workflow_handle(workflow_id)
            await handle.signal(ChatWorkflow.post_message, message, msg_id)
            print(f"DEBUG stream.py: Signal sent successfully for {msg_id}")

        # Stream responses from the pubsub
        print(f"DEBUG stream.py: Entering pubsub listen loop for {msg_id}")
        async for message in pubsub.listen():
            print(f"DEBUG stream.py: Received raw pubsub message: {message}")
            if message["type"] == "message":
                chunk = message["data"]
                print(
                    f"DEBUG stream.py: yielding chunk from Redis channel {msg_id}: {chunk[:30]}..."
                )
                yield chunk

                # A turn is finished when we see an 'end' event in the stream
                if '"type":"end"' in chunk or '"type": "end"' in chunk:
                    break

    except Exception as e:
        print(f"DEBUG stream.py: Exception in stream: {e}")
        error_event = ErrorEvent(message_id=msg_id, error=str(e))
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
        simulate_streaming_response(
            request.message,
            request.conversation_id,
            request.message_id,
        ),
        media_type="text/event-stream",
    )
