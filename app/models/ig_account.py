from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.ig_post import InstagramPost


def generate_cuid() -> str:
    """Generate a CUID-like unique identifier."""
    import uuid
    return str(uuid.uuid4()).replace("-", "")[:25]


class InstagramAccount(SQLModel, table=True):
    """Instagram Account database model."""

    __tablename__ = "instagram_accounts"

    id: str = Field(default_factory=generate_cuid, primary_key=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    full_name: str
    username: str = Field(unique=True, index=True)
    profile_pic_url: str
    posts_count: int = Field(default=0)
    followers_count: int = Field(default=0)
    follows_count: int = Field(default=0)
    biography: Optional[str] = Field(default=None)
    private: bool = Field(default=False)
    verified: bool = Field(default=False)
    is_business_account: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    user: "User" = Relationship(back_populates="instagram_accounts")
    posts: List["InstagramPost"] = Relationship(
        back_populates="instagram_account",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
