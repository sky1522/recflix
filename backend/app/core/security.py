"""
Security utilities for authentication
"""
import logging
import uuid
from datetime import datetime, timedelta
from typing import Optional

import bcrypt
from jose import JWTError, jwt

from app.config import settings

logger = logging.getLogger(__name__)

# JWT settings
ALGORITHM = settings.JWT_ALGORITHM
SECRET_KEY = settings.JWT_SECRET_KEY
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its hash"""
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )


def get_password_hash(password: str) -> str:
    """Hash a password"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    # Convert sub to string (JWT standard)
    if "sub" in to_encode:
        to_encode["sub"] = str(to_encode["sub"])
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT refresh token with jti for rotation."""
    to_encode = data.copy()
    # Convert sub to string (JWT standard)
    if "sub" in to_encode:
        to_encode["sub"] = str(to_encode["sub"])
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    jti = str(uuid.uuid4())
    to_encode.update({"exp": expire, "type": "refresh", "jti": jti})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    """Decode and verify a JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def _refresh_token_key(user_id: str) -> str:
    """Redis key for active refresh token jti."""
    return f"refresh_token:{user_id}"


async def store_refresh_jti(
    redis, user_id: str, jti: str, ttl_seconds: int,
) -> bool:
    """Store active refresh token jti in Redis. Returns True on success."""
    if not redis:
        return False
    try:
        await redis.setex(_refresh_token_key(user_id), ttl_seconds, jti)
        return True
    except Exception:
        logger.warning("Failed to store refresh jti in Redis")
        return False


async def validate_and_rotate_refresh(
    redis, user_id: str, jti: str,
) -> tuple[bool, bool]:
    """Validate refresh token jti and invalidate it.

    Returns (is_valid, is_compromised).
    - (True, False): jti matches, token consumed
    - (False, False): Redis unavailable, skip jti check (fallback)
    - (False, True): jti mismatch, possible token theft
    """
    if not redis:
        return False, False
    try:
        key = _refresh_token_key(user_id)
        raw = await redis.get(key)
        stored_jti = raw.decode() if isinstance(raw, bytes) else raw
        if stored_jti is None:
            # No record — token issued before rotation was enabled
            return False, False
        if stored_jti == jti:
            # Valid — delete immediately (one-time use)
            await redis.delete(key)
            return True, False
        # Mismatch — possible token theft; revoke all
        await redis.delete(key)
        return False, True
    except Exception:
        logger.warning("Redis error during refresh validation")
        return False, False


async def revoke_refresh_token(redis, user_id: str) -> None:
    """Revoke all refresh tokens for a user."""
    if not redis:
        return
    try:
        await redis.delete(_refresh_token_key(user_id))
    except Exception:
        pass
