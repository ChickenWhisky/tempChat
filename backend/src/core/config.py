from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Streaming AI Chatbot"
    API_V1_STR: str = "/api"
    # Ollama settings (PydanticAI connection)
    OLLAMA_BASE_URL: str = "http://ollama:11434/v1"
    OLLAMA_MODEL: str = "llama3.2"

    # Temporal configs
    TEMPORAL_HOST: str = "temporal:7233"
    TEMPORAL_TASK_QUEUE: str = "chat-task-queue"

    # Redis configs for PubSub
    REDIS_URL: str = "redis://temporal-redis:6379/0"

    class Config:
        case_sensitive = True


settings = Settings()
