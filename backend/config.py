import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = "gpt-4o"
    OPENAI_REALTIME_MODEL: str = "gpt-4o-realtime-preview"
    REALTIME_ENABLED: bool = os.getenv("REALTIME_ENABLED", "false").lower() == "true"

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "postgresql://postgres:password@localhost/jarvis"
    )
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")

    # JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # n8n
    N8N_API_URL: str = os.getenv("N8N_API_URL", "")
    N8N_API_KEY: str = os.getenv("N8N_API_KEY", "")

    # Smart Home
    SMART_HOME_API: str = os.getenv("SMART_HOME_API", "http://localhost:8001")

    # WebSocket
    WS_HEARTBEAT_INTERVAL: int = 30

    # App
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")


def get_settings() -> Settings:
    return Settings()
