from datetime import datetime
from typing import Optional, List

from sqlmodel import Session, select

from app.models.user import User
from app.schemas.user import UserCreate, UserCreateOAuth, UserUpdate
from app.core.security import hash_password, verify_password


def get_user_by_id(db: Session, user_id: str) -> Optional[User]:
    """Get a user by ID."""
    return db.get(User, user_id)


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Get a user by username."""
    statement = select(User).where(User.username == username)
    return db.exec(statement).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get a user by email."""
    statement = select(User).where(User.email == email)
    return db.exec(statement).first()


def get_user_by_oauth(db: Session, provider: str, provider_id: str) -> Optional[User]:
    """Get a user by OAuth provider and ID."""
    statement = select(User).where(
        User.oauth_provider == provider,
        User.oauth_provider_id == provider_id
    )
    return db.exec(statement).first()


def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
    """Get all users with pagination."""
    statement = select(User).offset(skip).limit(limit)
    return db.exec(statement).all()


def create_user(db: Session, user: UserCreate) -> User:
    """Create a new user."""
    db_user = User(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        password=hash_password(user.password),
        avatar=user.avatar,
        role=user.role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def create_user_oauth(db: Session, user: UserCreateOAuth) -> User:
    """Create a new user via OAuth."""
    db_user = User(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        avatar=user.avatar,
        oauth_provider=user.oauth_provider,
        oauth_provider_id=user.oauth_provider_id
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_user(db: Session, user_id: str, user_update: UserUpdate) -> Optional[User]:
    """Update a user."""
    db_user = get_user_by_id(db, user_id)
    if not db_user:
        return None
    
    update_data = user_update.model_dump(exclude_unset=True)
    if "password" in update_data and update_data["password"]:
        update_data["password"] = hash_password(update_data["password"])
    
    for key, value in update_data.items():
        setattr(db_user, key, value)
    
    db_user.updated_at = datetime.utcnow()
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def delete_user(db: Session, user_id: str) -> bool:
    """Delete a user."""
    db_user = get_user_by_id(db, user_id)
    if not db_user:
        return False
    
    db.delete(db_user)
    db.commit()
    return True


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """Authenticate a user."""
    user = get_user_by_username(db, username)
    if not user:
        return None
    if not user.password:
        return None  # OAuth user without password
    if not verify_password(password, user.password):
        return None
    return user
