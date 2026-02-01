from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class InstagramAccountBase(BaseModel):
    """Base Instagram Account schema."""
    full_name: str
    username: str
    profile_pic_url: str
    posts_count: int = 0
    followers_count: int = 0
    follows_count: int = 0
    biography: Optional[str] = None
    private: bool = False
    verified: bool = False
    is_business_account: bool = False


class InstagramAccountCreate(InstagramAccountBase):
    """Schema for creating an Instagram Account."""
    pass


class InstagramAccountUpdate(BaseModel):
    """Schema for updating an Instagram Account."""
    full_name: Optional[str] = None
    username: Optional[str] = None
    profile_pic_url: Optional[str] = None
    posts_count: Optional[int] = None
    followers_count: Optional[int] = None
    follows_count: Optional[int] = None
    biography: Optional[str] = None
    private: Optional[bool] = None
    verified: Optional[bool] = None
    is_business_account: Optional[bool] = None


class InstagramAccountRead(InstagramAccountBase):
    """Schema for reading an Instagram Account."""
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
