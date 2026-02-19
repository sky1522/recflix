"""
User API endpoints
"""
import json

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user
from app.core.rate_limit import limiter
from app.models import User
from app.schemas import UserResponse, UserUpdate, MBTIUpdate, OnboardingComplete

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
