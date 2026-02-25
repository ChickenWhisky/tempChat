from fastapi import APIRouter, HTTPException
from grpc import StatusCode
from src.core.temporal import TemporalClient
from src.workflows.chat import ChatWorkflow
from temporalio.service import RPCError

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
                print(
                    f"DEBUG history.py: Workflow {workflow_id} not found, returning empty history."
                )
                return []
            raise
    except Exception as e:
        print(f"DEBUG history.py: Exception getting history: {e}")
        # Re-raise standard exceptions so FastAPI returns a 500
        raise HTTPException(status_code=500, detail="Failed to retrieve history")
