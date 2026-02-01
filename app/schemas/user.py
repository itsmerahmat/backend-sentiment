from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr

from app.models.enums import UserRole


class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr
    username: str
    full_name: str


class UserCreate(UserBase):
    """Schema for creating a user."""
    password: str
    avatar: Optional[str] = None
    role: UserRole = UserRole.USER


class UserCreateOAuth(UserBase):
    """Schema for creating a user via OAuth."""
    avatar: Optional[str] = None
    oauth_provider: str
    oauth_provider_id: str


class UserUpdate(BaseModel):
    """Schema for updating a user."""
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    avatar: Optional[str] = None
    is_active: Optional[bool] = None


class UserRead(UserBase):
    """Schema for reading a user."""
    id: str
    avatar: Optional[str] = None
    role: UserRole
    is_active: bool
    oauth_provider: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    """Schema for user login."""
    username: str
    password: str


class Token(BaseModel):
    """Token schema."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token data schema."""
    username: Optional[str] = None
