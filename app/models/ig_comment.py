from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

from app.models.enums import SentimentLabel

if TYPE_CHECKING:
    from app.models.ig_post import InstagramPost


def generate_cuid() -> str:
    """Generate a CUID-like unique identifier."""
    import uuid
    return str(uuid.uuid4()).replace("-", "")[:25]


class InstagramComment(SQLModel, table=True):
    """Instagram Comment database model."""

    __tablename__ = "instagram_comments"

    id: str = Field(default_factory=generate_cuid, primary_key=True)
    instagram_post_id: str = Field(foreign_key="instagram_posts.id", index=True)
    comment_id: str = Field(unique=True, index=True)
    text: str
    owner_username: str
    likes_count: int = Field(default=0)
    sentiment_score: Optional[float] = Field(default=None)
    sentiment_label: Optional[SentimentLabel] = Field(default=None)
    timestamp: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    instagram_post: "InstagramPost" = Relationship(back_populates="comments")
