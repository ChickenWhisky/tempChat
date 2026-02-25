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
        self._history: list[ModelMessage] = []
        self._new_message: str | None = None
        self._message_id: str | None = None

    @workflow.signal
    def post_message(self, message: str, message_id: str) -> None:
        workflow.logger.warning(
            f"WORKFLOW DEBUG: post_message signal received for message_id: {message_id}"
        )
        self._new_message = message
        self._message_id = message_id

    @workflow.run
    async def run(self) -> None:
        """
        Maintains chat history and processes messages.
        """
        workflow.logger.warning("DURABLE_WORKFLOW: Started/Resumed.")

        while True:
            workflow.logger.warning("WORKFLOW DEBUG: Waiting for new message...")
            await workflow.wait_condition(lambda: self._new_message is not None)
            workflow.logger.warning(
                "WORKFLOW DEBUG: New message received, condition met."
            )

            msg = self._new_message
            msg_id = self._message_id
            self._new_message = None
            self._message_id = None

            if msg is None or msg_id is None:
                continue

            deps = ChatDeps(message_id=msg_id)

            # Run the agent with current history
            workflow.logger.warning(
                f"AGENT_RUN: Processing message {msg_id}. Current internal history size: {len(self._history)}"
            )
            result = await temporal_agent.run(
                msg, message_history=self._history, deps=deps
            )

            # Store the turn in history
            new_msgs = result.new_messages()
            workflow.logger.warning(
                f"AGENT_RUN: Completed {msg_id}. Adding {len(new_msgs)} new messages to durable history."
            )
            self._history.extend(new_msgs)
            workflow.logger.warning(
                f"AGENT_RUN: Total durable history size: {len(self._history)}"
            )
