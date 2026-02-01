from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.enums import SentimentLabel


class InstagramPostBase(BaseModel):
    """Base Instagram Post schema."""
    caption: Optional[str] = None
    owner_full_name: str
    owner_username: str
    display_url: Optional[str] = None
    video_url: Optional[str] = None
    url: str
    likes_count: int = 0
    comments_count: int = 0
    first_comment: Optional[str] = None
    timestamp: datetime


class InstagramPostCreate(InstagramPostBase):
    """Schema for creating an Instagram Post."""
    pass


class InstagramPostUpdate(BaseModel):
    """Schema for updating an Instagram Post."""
    caption: Optional[str] = None
    display_url: Optional[str] = None
    video_url: Optional[str] = None
    likes_count: Optional[int] = None
    comments_count: Optional[int] = None
    first_comment: Optional[str] = None
    sentiment_score: Optional[float] = None
    sentiment_label: Optional[SentimentLabel] = None


class InstagramPostRead(InstagramPostBase):
    """Schema for reading an Instagram Post."""
    id: str
    instagram_account_id: str
    sentiment_score: Optional[float] = None
    sentiment_label: Optional[SentimentLabel] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
