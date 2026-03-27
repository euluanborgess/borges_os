from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Default to SQLite for local dev/test. Production should override via .env / env vars.
    DATABASE_URL: str = "sqlite:///./borges_os.db"
    REDIS_URL: str = "redis://localhost:6379/0"
    OPENAI_API_KEY: str = ""
    LLM_MODEL: str = "gpt-4o-mini"

    # Public base URL used by external webhooks (Evolution -> Borges OS)
    # Set this in production to your public HTTPS URL (e.g. https://crm.seudominio.com)
    PUBLIC_BASE_URL: str = "http://localhost:8000"

    EVOLUTION_API_URL: str = "http://localhost:8080"
    EVOLUTION_API_KEY: str = ""

    # Meta Graph API
    META_APP_ID: str = ""
    META_APP_SECRET: str = ""

    SECRET_KEY: str = "changeit"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Bootstrap (first run)
    SEED_ADMIN_ON_STARTUP: bool = False
    DEFAULT_TENANT_NAME: str = "Sede Borges OS - Admin"
    DEFAULT_ADMIN_EMAIL: str = "admin@borges.com"
    DEFAULT_ADMIN_PASSWORD: str = "admin123456"
    DEFAULT_ADMIN_FULL_NAME: str = "Borges Super Admin"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
