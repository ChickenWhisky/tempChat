from temporalio import activity
import json
from src.services.llm_agent import stream_llm_response

@activity.defn
async def generate_llm_response_activity(message: str) -> str:
    """
    Temporal Activity that encapsulates the non-deterministic LLM call.
    It accumulated the streaming tokens internally and returns the final string.
    """
    full_response = ""
    # We iterate over the async generator directly
    async for chunk in stream_llm_response(message):
        # We only want the text content after "data: "
        if chunk.startswith("data: ") and chunk != "data: [DONE]\n\n":
            text = chunk[6:].strip()
            if text:
                try:
                    event_data = json.loads(text)
                    if event_data.get("type") == "token":
                        full_response += event_data.get("content", "")
                except json.JSONDecodeError:
                    pass
                
    return full_response
