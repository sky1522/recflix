"""
Authentication API endpoints
"""
import asyncio
import logging
import random
import secrets

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.config import settings
from app.core.deps import get_db
from app.core.http_client import get_http_client
from app.core.rate_limit import limiter
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    store_refresh_jti,
    validate_and_rotate_refresh,
    verify_password,
)
from app.models import User
from app.schemas import (
    SocialLoginRequest,
    SocialLoginResponse,
    Token,
    TokenRefresh,
    UserCreate,
    UserLogin,
    UserResponse,
)
from app.services.llm import get_redis_client

logger = logging.getLogger(__name__)

EXPERIMENT_GROUPS = ["control", "test_a", "test_b"]
_OAUTH_STATE_TTL = 600  # 10 minutes


def _weighted_random_group() -> str:
    """Select experiment group based on EXPERIMENT_WEIGHTS config.

    Format: "control:34,test_a:33,test_b:33" (weights, not percentages).
    Falls back to uniform random.choice if parsing fails.
    """
    weights_str = settings.EXPERIMENT_WEIGHTS
    if not weights_str:
        return random.choice(EXPERIMENT_GROUPS)
    try:
        parts = [p.strip().split(":") for p in weights_str.split(",")]
        groups = [p[0] for p in parts]
        weights = [int(p[1]) for p in parts]
        return random.choices(groups, weights=weights, k=1)[0]
    except (IndexError, ValueError):
        logger.warning("Invalid EXPERIMENT_WEIGHTS: %s, falling back to uniform", weights_str)
        return random.choice(EXPERIMENT_GROUPS)

router = APIRouter(prefix="/auth", tags=["Authentication"])


async def _create_oauth_state() -> str | None:
    """Generate a random state token and store it in Redis. Returns None if Redis unavailable."""
    redis = await get_redis_client()
    if not redis:
        return None
    state = secrets.token_urlsafe(32)
    try:
        await redis.setex(f"oauth_state:{state}", _OAUTH_STATE_TTL, "1")
        return state
    except Exception:
        logger.warning("Failed to store OAuth state in Redis")
        return None


async def _validate_oauth_state(state: str | None) -> bool:
    """Validate and consume an OAuth state token. Returns True if valid or if Redis is unavailable."""
    if not state:
        # No state provided — skip validation (backward compat)
        return True
    redis = await get_redis_client()
    if not redis:
        # Redis unavailable — skip validation, log warning
        logger.warning("Redis unavailable, skipping OAuth state validation")
        return True
    try:
        key = f"oauth_state:{state}"
        result = await redis.get(key)
        if result:
            await redis.delete(key)
            return True
        logger.warning("OAuth state mismatch or expired: %s…", state[:8])
        return False
    except Exception:
        logger.warning("Redis error during OAuth state validation")
        return True  # Fail open for availability


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def signup(request: Request, user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    # Check if email already exists
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create user with random experiment group
    hashed = await asyncio.to_thread(get_password_hash, user_data.password)
    user = User(
        email=user_data.email,
        password=hashed,
        nickname=user_data.nickname,
        mbti=user_data.mbti,
        birth_date=user_data.birth_date,
        location_consent=user_data.location_consent,
        experiment_group=_weighted_random_group(),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@router.post("/login", response_model=Token)
@limiter.limit("5/minute")
async def login(request: Request, credentials: UserLogin, db: Session = Depends(get_db)):
    """Login and get access token"""
    user = db.query(User).filter(User.email == credentials.email).first()

    is_valid = (
        user is not None
        and await asyncio.to_thread(verify_password, credentials.password, user.password)
    )
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )

    # Create tokens
    access_token = create_access_token(data={"sub": user.id})
    refresh_token = create_refresh_token(data={"sub": user.id})

    # Store refresh jti in Redis for rotation
    payload = decode_token(refresh_token)
    if payload and payload.get("jti"):
        redis = await get_redis_client()
        ttl = 7 * 24 * 3600  # REFRESH_TOKEN_EXPIRE_DAYS
        await store_refresh_jti(redis, str(user.id), payload["jti"], ttl)

    return Token(
        access_token=access_token,
        refresh_token=refresh_token
    )


@router.post("/refresh", response_model=Token)
@limiter.limit("5/minute")
async def refresh_token(request: Request, token_data: TokenRefresh, db: Session = Depends(get_db)):
    """Refresh access token using refresh token (with jti rotation)."""
    payload = decode_token(token_data.refresh_token)

    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )

    # Validate jti via Redis (rotation check)
    jti = payload.get("jti")
    redis = await get_redis_client()
    if jti and redis:
        is_valid, is_compromised = await validate_and_rotate_refresh(
            redis, str(user.id), jti,
        )
        if is_compromised:
            logger.warning("Refresh token reuse detected for user %s", user.id)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token reuse detected. Please login again.",
            )
        # is_valid=False + not compromised = Redis down or no record → fallback

    # Create new tokens
    access_token = create_access_token(data={"sub": user.id})
    new_refresh = create_refresh_token(data={"sub": user.id})

    # Store new jti
    new_payload = decode_token(new_refresh)
    if new_payload and new_payload.get("jti") and redis:
        ttl = 7 * 24 * 3600
        await store_refresh_jti(redis, str(user.id), new_payload["jti"], ttl)

    return Token(
        access_token=access_token,
        refresh_token=new_refresh,
    )


async def _build_social_response(user: User, is_new: bool) -> SocialLoginResponse:
    """Build SocialLoginResponse with JWT tokens (stores refresh jti)."""
    access_token = create_access_token(data={"sub": user.id})
    refresh_token_val = create_refresh_token(data={"sub": user.id})

    # Store refresh jti for rotation
    payload = decode_token(refresh_token_val)
    if payload and payload.get("jti"):
        redis = await get_redis_client()
        ttl = 7 * 24 * 3600
        await store_refresh_jti(redis, str(user.id), payload["jti"], ttl)

    return SocialLoginResponse(
        access_token=access_token,
        refresh_token=refresh_token_val,
        user=UserResponse.model_validate(user),
        is_new=is_new,
    )


@router.get("/kakao/authorize")
@limiter.limit("10/minute")
async def kakao_authorize(request: Request) -> dict[str, str]:
    """Generate Kakao OAuth authorize URL with CSRF state token."""
    params: dict[str, str] = {
        "client_id": settings.KAKAO_CLIENT_ID,
        "redirect_uri": settings.KAKAO_REDIRECT_URI,
        "response_type": "code",
    }
    state = await _create_oauth_state()
    if state:
        params["state"] = state
    qs = "&".join(f"{k}={v}" for k, v in params.items())
    return {"url": f"https://kauth.kakao.com/oauth/authorize?{qs}"}


@router.get("/google/authorize")
@limiter.limit("10/minute")
async def google_authorize(request: Request) -> dict[str, str]:
    """Generate Google OAuth authorize URL with CSRF state token."""
    params: dict[str, str] = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
    }
    state = await _create_oauth_state()
    if state:
        params["state"] = state
    qs = "&".join(f"{k}={v}" for k, v in params.items())
    return {"url": f"https://accounts.google.com/o/oauth2/v2/auth?{qs}"}


@router.post("/kakao", response_model=SocialLoginResponse)
@limiter.limit("10/minute")
async def kakao_login(
    request: Request,
    body: SocialLoginRequest,
    db: Session = Depends(get_db),
) -> SocialLoginResponse:
    """Login/Signup via Kakao OAuth"""
    # 0. Validate state (CSRF protection)
    if not await _validate_oauth_state(body.state):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "잘못된 인증 요청입니다. 다시 시도해주세요.")

    # 1. Exchange code for access_token
    client = get_http_client()
    token_resp = await client.post(
        "https://kauth.kakao.com/oauth/token",
        data={
            "grant_type": "authorization_code",
            "client_id": settings.KAKAO_CLIENT_ID,
            "client_secret": settings.KAKAO_CLIENT_SECRET,
            "redirect_uri": settings.KAKAO_REDIRECT_URI,
            "code": body.code,
        },
    )

    if token_resp.status_code != 200:
        logger.error("Kakao token exchange failed: %s", token_resp.text)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "카카오 인증에 실패했습니다.")

    kakao_access_token = token_resp.json().get("access_token")

    # 2. Get user info
    user_resp = await client.get(
        "https://kapi.kakao.com/v2/user/me",
        headers={"Authorization": f"Bearer {kakao_access_token}"},
    )

    if user_resp.status_code != 200:
        logger.error("Kakao user info failed: %s", user_resp.text)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "카카오 사용자 정보 조회에 실패했습니다.")

    kakao_data = user_resp.json()
    kakao_id = str(kakao_data["id"])
    kakao_account = kakao_data.get("kakao_account", {})
    profile = kakao_account.get("profile", {})

    # 3. Find or create user
    user = db.query(User).filter(User.kakao_id == kakao_id).first()
    if user:
        return await _build_social_response(user, is_new=False)

    # Check if email already exists (link accounts)
    email = kakao_account.get("email")
    if email:
        user = db.query(User).filter(User.email == email).first()
        if user:
            user.kakao_id = kakao_id
            user.profile_image = profile.get("profile_image_url")
            if user.auth_provider == "email":
                user.auth_provider = "kakao"
            db.commit()
            db.refresh(user)
            return await _build_social_response(user, is_new=False)

    # Create new user
    nickname = profile.get("nickname", f"kakao_{kakao_id[:8]}")
    if not email:
        email = f"kakao_{kakao_id}@noreply.example.com"

    user = User(
        email=email,
        password=await asyncio.to_thread(get_password_hash, secrets.token_urlsafe(32)),
        nickname=nickname,
        kakao_id=kakao_id,
        profile_image=profile.get("profile_image_url"),
        auth_provider="kakao",
        experiment_group=_weighted_random_group(),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return await _build_social_response(user, is_new=True)


@router.post("/google", response_model=SocialLoginResponse)
@limiter.limit("10/minute")
async def google_login(
    request: Request,
    body: SocialLoginRequest,
    db: Session = Depends(get_db),
) -> SocialLoginResponse:
    """Login/Signup via Google OAuth"""
    # 0. Validate state (CSRF protection)
    if not await _validate_oauth_state(body.state):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "잘못된 인증 요청입니다. 다시 시도해주세요.")

    # 1. Exchange code for access_token
    client = get_http_client()
    token_resp = await client.post(
        "https://oauth2.googleapis.com/token",
        data={
            "grant_type": "authorization_code",
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "code": body.code,
        },
    )

    if token_resp.status_code != 200:
        logger.error("Google token exchange failed: %s", token_resp.text)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "구글 인증에 실패했습니다.")

    google_access_token = token_resp.json().get("access_token")

    # 2. Get user info
    user_resp = await client.get(
        "https://www.googleapis.com/oauth2/v2/userinfo",
        headers={"Authorization": f"Bearer {google_access_token}"},
    )

    if user_resp.status_code != 200:
        logger.error("Google user info failed: %s", user_resp.text)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "구글 사용자 정보 조회에 실패했습니다.")

    google_data = user_resp.json()
    google_id = google_data["id"]
    email = google_data.get("email", "")
    name = google_data.get("name", f"google_{google_id[:8]}")
    picture = google_data.get("picture")

    # 3. Find or create user
    user = db.query(User).filter(User.google_id == google_id).first()
    if user:
        return await _build_social_response(user, is_new=False)

    # Check if email already exists (link accounts)
    if email:
        user = db.query(User).filter(User.email == email).first()
        if user:
            user.google_id = google_id
            user.profile_image = picture
            if user.auth_provider == "email":
                user.auth_provider = "google"
            db.commit()
            db.refresh(user)
            return await _build_social_response(user, is_new=False)

    # Create new user
    if not email:
        email = f"google_{google_id}@noreply.example.com"

    user = User(
        email=email,
        password=await asyncio.to_thread(get_password_hash, secrets.token_urlsafe(32)),
        nickname=name,
        google_id=google_id,
        profile_image=picture,
        auth_provider="google",
        experiment_group=_weighted_random_group(),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return await _build_social_response(user, is_new=True)
