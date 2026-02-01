from datetime import datetime
from typing import Optional, List

from sqlmodel import Session, select

from app.models.ig_account import InstagramAccount
from app.schemas.ig_account import InstagramAccountCreate, InstagramAccountUpdate


def get_account_by_id(db: Session, account_id: str) -> Optional[InstagramAccount]:
    """Get an Instagram account by ID."""
    return db.get(InstagramAccount, account_id)


def get_account_by_username(db: Session, username: str) -> Optional[InstagramAccount]:
    """Get an Instagram account by username."""
    statement = select(InstagramAccount).where(InstagramAccount.username == username)
    return db.exec(statement).first()


def get_accounts_by_user(db: Session, user_id: str, skip: int = 0, limit: int = 100) -> List[InstagramAccount]:
    """Get all Instagram accounts for a user."""
    statement = select(InstagramAccount).where(
        InstagramAccount.user_id == user_id
    ).offset(skip).limit(limit)
    return db.exec(statement).all()


def get_accounts(db: Session, skip: int = 0, limit: int = 100) -> List[InstagramAccount]:
    """Get all Instagram accounts with pagination."""
    statement = select(InstagramAccount).offset(skip).limit(limit)
    return db.exec(statement).all()


def create_account(db: Session, account: InstagramAccountCreate, user_id: str) -> InstagramAccount:
    """Create a new Instagram account."""
    db_account = InstagramAccount(
        user_id=user_id,
        full_name=account.full_name,
        username=account.username,
        profile_pic_url=account.profile_pic_url,
        posts_count=account.posts_count,
        followers_count=account.followers_count,
        follows_count=account.follows_count,
        biography=account.biography,
        private=account.private,
        verified=account.verified,
        is_business_account=account.is_business_account
    )
    db.add(db_account)
    db.commit()
    db.refresh(db_account)
    return db_account


def update_account(db: Session, account_id: str, account_update: InstagramAccountUpdate) -> Optional[InstagramAccount]:
    """Update an Instagram account."""
    db_account = get_account_by_id(db, account_id)
    if not db_account:
        return None
    
    update_data = account_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_account, key, value)
    
    db_account.updated_at = datetime.utcnow()
    db.add(db_account)
    db.commit()
    db.refresh(db_account)
    return db_account


def delete_account(db: Session, account_id: str) -> bool:
    """Delete an Instagram account."""
    db_account = get_account_by_id(db, account_id)
    if not db_account:
        return False
    
    db.delete(db_account)
    db.commit()
    return True
