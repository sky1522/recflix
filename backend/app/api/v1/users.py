"""
User API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user
from app.models import User
from app.schemas import UserResponse, UserUpdate, MBTIUpdate

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user's information"""
    return current_user


@router.put("/me", response_model=UserResponse)
def update_current_user(
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
def update_mbti(
    mbti_data: MBTIUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user's MBTI"""
    current_user.mbti = mbti_data.mbti
    db.commit()
    db.refresh(current_user)

    return current_user
