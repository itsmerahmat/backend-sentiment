from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlmodel import Field, Relationship, SQLModel

from app.models.enums import SentimentLabel

if TYPE_CHECKING:
    from app.models.ig_account import InstagramAccount
    from app.models.ig_comment import InstagramComment


def generate_cuid() -> str:
    """Generate a CUID-like unique identifier."""
    import uuid
    return str(uuid.uuid4()).replace("-", "")[:25]


class InstagramPost(SQLModel, table=True):
    """Instagram Post database model."""

    __tablename__ = "instagram_posts"

    id: str = Field(default_factory=generate_cuid, primary_key=True)
    instagram_account_id: str = Field(foreign_key="instagram_accounts.id", index=True)
    caption: Optional[str] = Field(default=None)
    owner_full_name: str
    owner_username: str
    display_url: Optional[str] = Field(default=None)
    video_url: Optional[str] = Field(default=None)
    url: str = Field(unique=True, index=True)
    likes_count: int = Field(default=0)
    comments_count: int = Field(default=0)
    first_comment: Optional[str] = Field(default=None)
    sentiment_score: Optional[float] = Field(default=None)
    sentiment_label: Optional[SentimentLabel] = Field(default=None)
    timestamp: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    instagram_account: "InstagramAccount" = Relationship(back_populates="posts")
    comments: List["InstagramComment"] = Relationship(
        back_populates="instagram_post",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
