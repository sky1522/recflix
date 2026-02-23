"""
User API endpoints
"""
import json
import logging

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.core.rate_limit import limiter
from app.core.security import revoke_refresh_token
from app.models import User, UserEvent
from app.schemas import MBTIUpdate, OnboardingComplete, UserResponse, UserUpdate
from app.services.llm import get_redis_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
@limiter.limit("30/minute")
def get_current_user_info(request: Request, current_user: User = Depends(get_current_user)):
    """Get current user's information"""
    return current_user


@router.put("/me", response_model=UserResponse)
@limiter.limit("30/minute")
def update_current_user(
    request: Request,
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user's information"""
    ALLOWED_UPDATE_FIELDS = {"nickname", "mbti", "birth_date", "location_consent"}
    update_data = user_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        if field in ALLOWED_UPDATE_FIELDS:
            setattr(current_user, field, value)

    db.commit()
    db.refresh(current_user)

    return current_user


@router.put("/me/mbti", response_model=UserResponse)
@limiter.limit("30/minute")
def update_mbti(
    request: Request,
    mbti_data: MBTIUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user's MBTI"""
    current_user.mbti = mbti_data.mbti
    db.commit()
    db.refresh(current_user)

    return current_user


@router.put("/me/onboarding-complete", response_model=UserResponse)
@limiter.limit("10/minute")
def complete_onboarding(
    request: Request,
    body: OnboardingComplete,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserResponse:
    """Mark onboarding as completed and save preferred genres"""
    current_user.onboarding_completed = True
    current_user.preferred_genres = json.dumps(body.preferred_genres, ensure_ascii=False)
    db.commit()
    db.refresh(current_user)
    return current_user


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("3/minute")
async def delete_account(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    """Delete current user account and all associated data (GDPR hard delete).

    Cascade order:
    1. user_events (SET NULL FK, explicitly deleted for GDPR)
    2. ratings (CASCADE FK, auto-deleted)
    3. collections + collection_movies (CASCADE FK, auto-deleted)
    4. user record
    """
    user_id = current_user.id
    try:
        # 1. Explicitly delete user_events (FK is SET NULL, not CASCADE)
        db.query(UserEvent).filter(UserEvent.user_id == user_id).delete()

        # 2-4. Delete user (ratings + collections cascade automatically)
        db.delete(current_user)
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Failed to delete account for user %s", user_id)
        raise

    # 5. Clean up Redis (refresh token, best-effort)
    try:
        redis = await get_redis_client()
        await revoke_refresh_token(redis, str(user_id))
    except Exception:
        logger.warning("Failed to revoke Redis tokens for deleted user %s", user_id)

    logger.info("Account deleted: user_id=%s", user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
