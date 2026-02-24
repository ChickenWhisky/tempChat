from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    PROJECT_NAME: str = "Streaming AI Chatbot"
    API_V1_STR: str = "/api"
    # Ollama settings (PydanticAI connection)
    OLLAMA_BASE_URL: str = "http://ollama:11434/v1"
    OLLAMA_MODEL: str = "llama3.2"
    
    # Temporal Settings
    TEMPORAL_HOST: str = "temporal:7233"
    TEMPORAL_TASK_QUEUE: str = "chat-task-queue"

    # Allow local frontend development by default
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    class Config:
        case_sensitive = True

settings = Settings()
