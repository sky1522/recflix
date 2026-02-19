"""
Authentication API endpoints
"""
import logging
import random
import secrets

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.config import settings
from app.core.deps import get_db
from app.core.rate_limit import limiter
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
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

logger = logging.getLogger(__name__)

EXPERIMENT_GROUPS = ["control", "test_a", "test_b"]

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
def signup(request: Request, user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    # Check if email already exists
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create user with random experiment group
    user = User(
        email=user_data.email,
        password=get_password_hash(user_data.password),
        nickname=user_data.nickname,
        mbti=user_data.mbti,
        birth_date=user_data.birth_date,
        location_consent=user_data.location_consent,
        experiment_group=random.choice(EXPERIMENT_GROUPS),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@router.post("/login", response_model=Token)
@limiter.limit("5/minute")
def login(request: Request, credentials: UserLogin, db: Session = Depends(get_db)):
    """Login and get access token"""
    user = db.query(User).filter(User.email == credentials.email).first()

    if not user or not verify_password(credentials.password, user.password):
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

    return Token(
        access_token=access_token,
        refresh_token=refresh_token
    )


@router.post("/refresh", response_model=Token)
@limiter.limit("5/minute")
def refresh_token(request: Request, token_data: TokenRefresh, db: Session = Depends(get_db)):
    """Refresh access token using refresh token"""
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

    # Create new tokens
    access_token = create_access_token(data={"sub": user.id})
    refresh_token = create_refresh_token(data={"sub": user.id})

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
    )


def _build_social_response(user: User, is_new: bool) -> SocialLoginResponse:
    """Build SocialLoginResponse with JWT tokens."""
    access_token = create_access_token(data={"sub": user.id})
    refresh_token_val = create_refresh_token(data={"sub": user.id})
    return SocialLoginResponse(
        access_token=access_token,
        refresh_token=refresh_token_val,
        user=UserResponse.model_validate(user),
        is_new=is_new,
    )


@router.post("/kakao", response_model=SocialLoginResponse)
@limiter.limit("10/minute")
def kakao_login(
    request: Request,
    body: SocialLoginRequest,
    db: Session = Depends(get_db),
) -> SocialLoginResponse:
    """Login/Signup via Kakao OAuth"""
    # 1. Exchange code for access_token
    with httpx.Client(timeout=10.0) as client:
        token_resp = client.post(
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
    with httpx.Client(timeout=10.0) as client:
        user_resp = client.get(
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
        return _build_social_response(user, is_new=False)

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
            return _build_social_response(user, is_new=False)

    # Create new user
    nickname = profile.get("nickname", f"kakao_{kakao_id[:8]}")
    if not email:
        email = f"kakao_{kakao_id}@recflix.local"

    user = User(
        email=email,
        password=get_password_hash(secrets.token_urlsafe(32)),
        nickname=nickname,
        kakao_id=kakao_id,
        profile_image=profile.get("profile_image_url"),
        auth_provider="kakao",
        experiment_group=random.choice(EXPERIMENT_GROUPS),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return _build_social_response(user, is_new=True)


@router.post("/google", response_model=SocialLoginResponse)
@limiter.limit("10/minute")
def google_login(
    request: Request,
    body: SocialLoginRequest,
    db: Session = Depends(get_db),
) -> SocialLoginResponse:
    """Login/Signup via Google OAuth"""
    # 1. Exchange code for access_token
    with httpx.Client(timeout=10.0) as client:
        token_resp = client.post(
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
    with httpx.Client(timeout=10.0) as client:
        user_resp = client.get(
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
        return _build_social_response(user, is_new=False)

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
            return _build_social_response(user, is_new=False)

    # Create new user
    if not email:
        email = f"google_{google_id}@recflix.local"

    user = User(
        email=email,
        password=get_password_hash(secrets.token_urlsafe(32)),
        nickname=name,
        google_id=google_id,
        profile_image=picture,
        auth_provider="google",
        experiment_group=random.choice(EXPERIMENT_GROUPS),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return _build_social_response(user, is_new=True)
