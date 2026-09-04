"""Database Models — SQLAlchemy pour User, Session, et RAG (Document)."""

import logging
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker
from pgvector.sqlalchemy import Vector
from backend.config import get_settings

logger = logging.getLogger(__name__)
Base = declarative_base()

EMBEDDING_DIM = 1536  # text-embedding-3-small


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    gmail_token = Column(Text, nullable=True)  # OAuth token for Gmail API
    created_at = Column(DateTime, default=datetime.utcnow)


class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)


class Document(Base):
    """RAG (T2) — chunks indexés (synthèses e-mails, exports sessions/*.md)."""

    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    embedding = Column(Vector(EMBEDDING_DIM), nullable=False)
    source = Column(String, nullable=False, index=True)  # "email" | "session"
    external_id = Column(String, nullable=True, index=True)  # id source (dédup / upsert)
    doc_metadata = Column("metadata", JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# Initialize DB engine
settings = get_settings()
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Create all tables on startup. Active l'extension pgvector si absente."""
    try:
        with engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            conn.commit()
    except Exception as e:
        # Pas bloquant pour User/Session — juste le RAG qui restera indisponible.
        logger.warning(f"Extension pgvector indisponible ({e}) — RAG désactivé tant que non résolu.")
    Base.metadata.create_all(bind=engine)
