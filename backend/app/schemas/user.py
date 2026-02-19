"""
User Pydantic Schemas
"""
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator


class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr
    nickname: str = Field(..., min_length=2, max_length=50)
    mbti: Optional[str] = Field(None, pattern=r'^[EI][NS][TF][JP]$')
    birth_date: Optional[date] = None
    location_consent: bool = False


class UserCreate(UserBase):
    """Schema for user registration"""
    password: str = Field(..., min_length=6, max_length=100)


class UserUpdate(BaseModel):
    """Schema for user update"""
    nickname: Optional[str] = Field(None, min_length=2, max_length=50)
    mbti: Optional[str] = Field(None, pattern=r'^[EI][NS][TF][JP]$')
    birth_date: Optional[date] = None
    location_consent: Optional[bool] = None


class UserResponse(BaseModel):
    """Schema for user response"""
    id: int
    email: EmailStr
    nickname: str
    mbti: Optional[str]
    birth_date: Optional[date]
    location_consent: bool
    auth_provider: str = "email"
    profile_image: Optional[str] = None
    onboarding_completed: bool = False
    preferred_genres: Optional[list[str]] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

    @field_validator("preferred_genres", mode="before")
    @classmethod
    def parse_preferred_genres(cls, v: object) -> Optional[list[str]]:
        import json
        if isinstance(v, str):
            return json.loads(v)
        return v


class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str


class Token(BaseModel):
    """Schema for JWT tokens"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefresh(BaseModel):
    """Schema for token refresh"""
    refresh_token: str


class MBTIUpdate(BaseModel):
    """Schema for MBTI update"""
    mbti: str = Field(..., pattern=r'^[EI][NS][TF][JP]$')


class SocialLoginRequest(BaseModel):
    """Schema for social login (Kakao/Google)"""
    code: str = Field(..., min_length=1)


class SocialLoginResponse(BaseModel):
    """Schema for social login response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse
    is_new: bool


class OnboardingComplete(BaseModel):
    """Schema for onboarding completion"""
    preferred_genres: list[str] = Field(..., min_length=1)
