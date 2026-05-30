"""Auth Service — JWT token generation/validation + user management."""

from datetime import datetime, timedelta
from typing import Optional
import os
import jwt
from backend.config import get_settings
from backend.models import User, SessionLocal, engine, Base

settings = get_settings()


def create_jwt_token(user_id: int) -> str:
    """Create JWT token for user_id."""
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        "iat": datetime.utcnow(),
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token


def verify_jwt_token(token: str) -> Optional[int]:
    """Verify JWT token and return user_id."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("user_id")
        if user_id is None:
            return None
        return user_id
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


async def ensure_demo_user_exists(email: str) -> tuple[int, str]:
    """
    Create user if not exists, return (user_id, jwt_token).
    This is for hackathon: single preconfigured user.
    """
    # Create tables if needed
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Check if user exists
        user = db.query(User).filter(User.email == email).first()
        if user is None:
            # Create new user
            user = User(email=email)
            db.add(user)
            db.commit()
            db.refresh(user)

        # Generate token
        token = create_jwt_token(user.id)
        return user.id, token
    finally:
        db.close()
