from pydantic_ai.messages import ModelMessage
from temporalio import workflow
import logging
from src.services.llm_agent import temporal_agent, ChatDeps
from pydantic_ai.durable_exec.temporal import PydanticAIWorkflow

# Configure logger
logger = logging.getLogger(__name__)


@workflow.defn
class ChatWorkflow(PydanticAIWorkflow):
    __pydantic_ai_agents__ = [temporal_agent]

    def __init__(self) -> None:
        """
        Initializes the workflow with empty history and no pending messages.
        """
        self._history: list[ModelMessage] = []
        self._new_message: str | None = None
        self._message_id: str | None = None

    @workflow.signal
    def post_message(self, message: str, message_id: str) -> None:
        """
        Signal to post a new message to the conversation.
        """
        self._new_message = message
        self._message_id = message_id

    @workflow.query
    def get_history(self) -> list[ModelMessage]:
        """
        Query to retrieve the current chat history.
        """
        return self._history

    @workflow.run
    async def run(self) -> None:
        """
        Maintains chat history and processes messages.
        """
        while True:
            await workflow.wait_condition(lambda: self._new_message is not None)

            msg = self._new_message
            msg_id = self._message_id
            self._new_message = None
            self._message_id = None

            if msg is None or msg_id is None:
                continue

            deps = ChatDeps(message_id=msg_id)

            # Run the agent with current history
            result = await temporal_agent.run(
                msg, message_history=self._history, deps=deps
            )

            # Store the turn in history
            new_msgs = result.new_messages()
            self._history.extend(new_msgs)
