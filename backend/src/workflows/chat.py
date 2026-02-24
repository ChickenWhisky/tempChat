from pydantic_ai.messages import ModelMessage
from temporalio import workflow

from src.services.llm_agent import temporal_agent, ChatDeps


from pydantic_ai.durable_exec.temporal import PydanticAIWorkflow


@workflow.defn
class ChatWorkflow(PydanticAIWorkflow):
    __pydantic_ai_agents__ = [temporal_agent]

    @workflow.run
    async def run(
        self,
        message: str,
        message_id: str,
        message_history: list[ModelMessage] | None = None,
    ) -> str:
        """
        Executes the AI Agent durably.
        """
        deps = ChatDeps(message_id=message_id, message_history=message_history)

        # The agent runs durably. Tools become localized Temporal activities automatically.
        result = await temporal_agent.run(message, deps=deps)
        return result.output
