import logging
from fastapi import APIRouter, HTTPException
from grpc import StatusCode
from src.core.temporal import TemporalClient
from src.workflows.chat import ChatWorkflow
from temporalio.service import RPCError

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/{conversation_id}/history", summary="Get chat history")
async def get_chat_history(conversation_id: str):
    """
    Retrieve the durable chat history for a conversation using a Temporal Query.
    Returns an empty list if the conversation hasn't started yet.
    """
    try:
        client = await TemporalClient.get_client()
        workflow_id = f"chat-{conversation_id}"
        handle = client.get_workflow_handle(workflow_id)

        # We need to handle the case where the workflow doesn't exist yet.
        # Temporal raises an RPCError with NOT_FOUND status in this case.
        try:
            history = await handle.query(ChatWorkflow.get_history)
            return history
        except RPCError as e:
            if (
                getattr(e, "status", None) == StatusCode.NOT_FOUND
                or "not found" in str(e).lower()
            ):
                return []
            raise
    except Exception as e:
        logger.error(f"Exception getting history for {conversation_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve history")


@router.delete(
    "/{conversation_id}", summary="Delete a conversation and terminate its workflow"
)
async def delete_conversation(conversation_id: str):
    """
    Terminates the durable Temporal workflow associated with the conversation.
    """
    try:
        client = await TemporalClient.get_client()
        workflow_id = f"chat-{conversation_id}"
        handle = client.get_workflow_handle(workflow_id)

        try:
            await handle.terminate(reason="User deleted conversation from UI")
            logger.info(f"Successfully terminated workflow {workflow_id}")
            return {
                "status": "success",
                "message": f"Conversation {conversation_id} deleted",
            }
        except RPCError as e:
            if (
                getattr(e, "status", None) == StatusCode.NOT_FOUND
                or "not found" in str(e).lower()
            ):
                return {
                    "status": "success",
                    "message": f"Conversation {conversation_id} was already gone",
                }
            raise
    except Exception as e:
        logger.error(f"Exception terminating workflow for {conversation_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete conversation")
