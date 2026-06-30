from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/crisisradar"
    redis_url: str = "redis://localhost:6379/0"
    openai_api_key: str | None = None
    default_embedding_model: str = "text-embedding-3-small"
    default_llm_model: str = "gpt-4o-mini"
    app_name: str = "Crisis Radar VE"
    debug: bool = True

    class Config:
        env_file = ".env"


settings = Settings()
