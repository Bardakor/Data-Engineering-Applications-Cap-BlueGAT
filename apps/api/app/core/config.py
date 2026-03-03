from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "Nugget Data & AI Initiative API"
    api_prefix: str = "/api/v1"
    database_url: str = "postgresql+psycopg://nugget:nugget@localhost:5432/nugget"
    cors_origins: str = "http://localhost:3000"
    openai_api_key: str | None = None
    openai_rag_model: str = "gpt-4.1-mini"
    openai_embedding_model: str = "text-embedding-3-small"
    seed_on_startup: bool = False

    # Ollama (local LLM) - used for RAG answers when OpenAI is not configured
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_chat_model: str = "tinyllama"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
