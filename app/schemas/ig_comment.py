from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.enums import SentimentLabel


class InstagramCommentBase(BaseModel):
    """Base Instagram Comment schema."""
    comment_id: str
    text: str
    owner_username: str
    likes_count: int = 0
    timestamp: datetime


class InstagramCommentCreate(InstagramCommentBase):
    """Schema for creating an Instagram Comment."""
    pass


class InstagramCommentUpdate(BaseModel):
    """Schema for updating an Instagram Comment."""
    text: Optional[str] = None
    likes_count: Optional[int] = None
    sentiment_score: Optional[float] = None
    sentiment_label: Optional[SentimentLabel] = None


class InstagramCommentRead(InstagramCommentBase):
    """Schema for reading an Instagram Comment."""
    id: str
    instagram_post_id: str
    sentiment_score: Optional[float] = None
    sentiment_label: Optional[SentimentLabel] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
