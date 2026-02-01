from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlmodel import Field, Relationship, SQLModel

from app.models.enums import UserRole

if TYPE_CHECKING:
    from app.models.ig_account import InstagramAccount


def generate_cuid() -> str:
    """Generate a CUID-like unique identifier."""
    import uuid
    return str(uuid.uuid4()).replace("-", "")[:25]


class User(SQLModel, table=True):
    """User database model."""

    __tablename__ = "users"

    id: str = Field(default_factory=generate_cuid, primary_key=True)
    email: str = Field(unique=True, index=True)
    username: str = Field(unique=True, index=True)
    full_name: str
    password: Optional[str] = Field(default=None)  # Hashed password (null for OAuth users)
    avatar: Optional[str] = Field(default=None)  # URL to avatar image
    role: UserRole = Field(default=UserRole.USER)
    is_active: bool = Field(default=True)
    oauth_provider: Optional[str] = Field(default=None, index=True)  # google, github, etc
    oauth_provider_id: Optional[str] = Field(default=None)  # Provider's user ID
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    instagram_accounts: List["InstagramAccount"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
