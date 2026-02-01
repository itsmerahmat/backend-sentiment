from datetime import datetime
from typing import Optional, List

from sqlmodel import Session, select

from app.models.ig_post import InstagramPost
from app.schemas.ig_post import InstagramPostCreate, InstagramPostUpdate


def get_post_by_id(db: Session, post_id: str) -> Optional[InstagramPost]:
    """Get an Instagram post by ID."""
    return db.get(InstagramPost, post_id)


def get_post_by_url(db: Session, url: str) -> Optional[InstagramPost]:
    """Get an Instagram post by URL."""
    statement = select(InstagramPost).where(InstagramPost.url == url)
    return db.exec(statement).first()


def get_posts_by_account(db: Session, account_id: str, skip: int = 0, limit: int = 100) -> List[InstagramPost]:
    """Get all Instagram posts for an account."""
    statement = select(InstagramPost).where(
        InstagramPost.instagram_account_id == account_id
    ).order_by(InstagramPost.timestamp.desc()).offset(skip).limit(limit)
    return db.exec(statement).all()


def get_posts(db: Session, skip: int = 0, limit: int = 100) -> List[InstagramPost]:
    """Get all Instagram posts with pagination."""
    statement = select(InstagramPost).order_by(InstagramPost.timestamp.desc()).offset(skip).limit(limit)
    return db.exec(statement).all()


def create_post(db: Session, post: InstagramPostCreate, account_id: str) -> InstagramPost:
    """Create a new Instagram post."""
    db_post = InstagramPost(
        instagram_account_id=account_id,
        caption=post.caption,
        owner_full_name=post.owner_full_name,
        owner_username=post.owner_username,
        display_url=post.display_url,
        video_url=post.video_url,
        url=post.url,
        likes_count=post.likes_count,
        comments_count=post.comments_count,
        first_comment=post.first_comment,
        timestamp=post.timestamp
    )
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post


def create_posts_bulk(db: Session, posts: List[InstagramPostCreate], account_id: str) -> List[InstagramPost]:
    """Create multiple Instagram posts at once."""
    db_posts = []
    for post in posts:
        db_post = InstagramPost(
            instagram_account_id=account_id,
            caption=post.caption,
            owner_full_name=post.owner_full_name,
            owner_username=post.owner_username,
            display_url=post.display_url,
            video_url=post.video_url,
            url=post.url,
            likes_count=post.likes_count,
            comments_count=post.comments_count,
            first_comment=post.first_comment,
            timestamp=post.timestamp
        )
        db.add(db_post)
        db_posts.append(db_post)
    
    db.commit()
    for db_post in db_posts:
        db.refresh(db_post)
    return db_posts


def update_post(db: Session, post_id: str, post_update: InstagramPostUpdate) -> Optional[InstagramPost]:
    """Update an Instagram post."""
    db_post = get_post_by_id(db, post_id)
    if not db_post:
        return None
    
    update_data = post_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_post, key, value)
    
    db_post.updated_at = datetime.utcnow()
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post


def delete_post(db: Session, post_id: str) -> bool:
    """Delete an Instagram post."""
    db_post = get_post_by_id(db, post_id)
    if not db_post:
        return False
    
    db.delete(db_post)
    db.commit()
    return True


def get_posts_without_sentiment(db: Session, limit: int = 100) -> List[InstagramPost]:
    """Get posts that don't have sentiment analysis yet."""
    statement = select(InstagramPost).where(
        InstagramPost.sentiment_label == None
    ).limit(limit)
    return db.exec(statement).all()
