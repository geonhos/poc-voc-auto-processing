"""
Application Configuration
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""

    # Database
    database_url: str = "sqlite+aiosqlite:///./voc.db"

    # LLM
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "gpt-oss:20b"

    # Slack
    slack_webhook_url: str = ""

    # RAG & Vector DB
    chroma_persist_directory: str = "./data/chroma"
    embedding_model: str = "paraphrase-multilingual-MiniLM-L12-v2"
    similarity_top_k: int = 5
    similarity_threshold: float = 0.7

    # Application
    debug: bool = True
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
