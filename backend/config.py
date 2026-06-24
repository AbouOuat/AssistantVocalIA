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

    # ── Profil client ──────────────────────────────────────────
    CLIENT_NAME: str = os.getenv("CLIENT_NAME", "Abo")
    CLIENT_TIMEZONE: str = os.getenv("CLIENT_TIMEZONE", "Europe/Paris")
    CLIENT_LANGUAGE: str = os.getenv("CLIENT_LANGUAGE", "fr")

    # Boîtes mail
    CLIENT_OUTLOOK_MAILBOX: str = os.getenv("CLIENT_OUTLOOK_MAILBOX", "")
    CLIENT_SUMMARY_RECIPIENT: str = os.getenv(
        "CLIENT_SUMMARY_RECIPIENT", os.getenv("SUMMARY_RECIPIENT_EMAIL", "")
    )
    CLIENT_CR_RECIPIENT: str = os.getenv("CLIENT_CR_RECIPIENT", "")
    CLIENT_GMAIL: str = os.getenv("CLIENT_GMAIL", os.getenv("GMAIL_USER_EMAIL", ""))

    # Agenda
    CLIENT_CALENDAR_ID: str = os.getenv("CLIENT_CALENDAR_ID", "primary")

    # Classifier Outlook — keywords configurables par client
    CLIENT_URGENCY_KEYWORDS: str = os.getenv(
        "CLIENT_URGENCY_KEYWORDS",
        "assignation,convocation,jugement,ordonnance,huissier,audience,appel,arrêt,décision,notification",
    )
    CLIENT_EXCLUDED_DOMAINS: str = os.getenv(
        "CLIENT_EXCLUDED_DOMAINS",
        "substack.com,mailchimp.com,sendgrid.net,newsletter,noreply",
    )

    # Technique
    ALLOWED_ORIGINS: str = os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:3000,http://localhost:5173,http://145.223.34.178:3000,http://145.223.34.178,https://jarvis.obyz.biz,http://jarvis.obyz.biz",
    )
    EMAIL_ANALYSIS_CACHE_TTL: int = int(os.getenv("EMAIL_ANALYSIS_CACHE_TTL", "86400"))
    EMAIL_INBOX_CACHE_TTL: int = int(os.getenv("EMAIL_INBOX_CACHE_TTL", "120"))

    # Version workflows n8n — v1 = custom JS, v2 = LangChain natif
    WORKFLOW_VERSION: str = os.getenv("WORKFLOW_VERSION", "v1")


def get_settings() -> Settings:
    return Settings()
