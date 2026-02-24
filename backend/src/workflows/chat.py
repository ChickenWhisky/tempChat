from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from src.activities.llm import generate_llm_response_activity

@workflow.defn
class ChatWorkflow:
    @workflow.run
    async def run(self, message: str) -> str:
        """
        The deterministic workflow logic. 
        Executes the non-deterministic LLM activity and durably returns the result.
        """
        # Set a generous timeout since LLM generation can take time depending on hardware
        llm_response = await workflow.execute_activity(
            generate_llm_response_activity,
            message,
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=RetryPolicy(
                initial_interval=timedelta(seconds=2),
                backoff_coefficient=2.0,
                maximum_attempts=3, # Retry up to 3 times on transient API failures
            )
        )
        return llm_response
