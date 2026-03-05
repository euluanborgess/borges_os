from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Default to SQLite for local dev/test. Production should override via .env / env vars.
    DATABASE_URL: str = "sqlite:///./borges_os.db"
    REDIS_URL: str = "redis://localhost:6379/0"
    OPENAI_API_KEY: str = ""
    LLM_MODEL: str = "gpt-4.1-mini"
    
    EVOLUTION_API_URL: str = "http://localhost:8080"
    EVOLUTION_API_KEY: str = ""

    SECRET_KEY: str = "changeit"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"

settings = Settings()
