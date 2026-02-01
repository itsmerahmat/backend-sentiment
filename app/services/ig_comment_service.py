from datetime import datetime
from typing import Optional, List

from sqlmodel import Session, select

from app.models.ig_comment import InstagramComment
from app.schemas.ig_comment import InstagramCommentCreate, InstagramCommentUpdate


def get_comment_by_id(db: Session, comment_id: str) -> Optional[InstagramComment]:
    """Get an Instagram comment by ID."""
    return db.get(InstagramComment, comment_id)


def get_comment_by_comment_id(db: Session, comment_id: str) -> Optional[InstagramComment]:
    """Get an Instagram comment by Instagram comment ID."""
    statement = select(InstagramComment).where(InstagramComment.comment_id == comment_id)
    return db.exec(statement).first()


def get_comments_by_post(db: Session, post_id: str, skip: int = 0, limit: int = 100) -> List[InstagramComment]:
    """Get all Instagram comments for a post."""
    statement = select(InstagramComment).where(
        InstagramComment.instagram_post_id == post_id
    ).order_by(InstagramComment.timestamp.desc()).offset(skip).limit(limit)
    return db.exec(statement).all()


def get_comments(db: Session, skip: int = 0, limit: int = 100) -> List[InstagramComment]:
    """Get all Instagram comments with pagination."""
    statement = select(InstagramComment).order_by(InstagramComment.timestamp.desc()).offset(skip).limit(limit)
    return db.exec(statement).all()


def create_comment(db: Session, comment: InstagramCommentCreate, post_id: str) -> InstagramComment:
    """Create a new Instagram comment."""
    db_comment = InstagramComment(
        instagram_post_id=post_id,
        comment_id=comment.comment_id,
        text=comment.text,
        owner_username=comment.owner_username,
        likes_count=comment.likes_count,
        timestamp=comment.timestamp
    )
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    return db_comment


def create_comments_bulk(db: Session, comments: List[InstagramCommentCreate], post_id: str) -> List[InstagramComment]:
    """Create multiple Instagram comments at once."""
    db_comments = []
    for comment in comments:
        # Skip if comment already exists
        existing = get_comment_by_comment_id(db, comment.comment_id)
        if existing:
            continue
            
        db_comment = InstagramComment(
            instagram_post_id=post_id,
            comment_id=comment.comment_id,
            text=comment.text,
            owner_username=comment.owner_username,
            likes_count=comment.likes_count,
            timestamp=comment.timestamp
        )
        db.add(db_comment)
        db_comments.append(db_comment)
    
    db.commit()
    for db_comment in db_comments:
        db.refresh(db_comment)
    return db_comments


def update_comment(db: Session, comment_id: str, comment_update: InstagramCommentUpdate) -> Optional[InstagramComment]:
    """Update an Instagram comment."""
    db_comment = get_comment_by_id(db, comment_id)
    if not db_comment:
        return None
    
    update_data = comment_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_comment, key, value)
    
    db_comment.updated_at = datetime.utcnow()
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    return db_comment


def delete_comment(db: Session, comment_id: str) -> bool:
    """Delete an Instagram comment."""
    db_comment = get_comment_by_id(db, comment_id)
    if not db_comment:
        return False
    
    db.delete(db_comment)
    db.commit()
    return True


def get_comments_without_sentiment(db: Session, limit: int = 100) -> List[InstagramComment]:
    """Get comments that don't have sentiment analysis yet."""
    statement = select(InstagramComment).where(
        InstagramComment.sentiment_label == None
    ).limit(limit)
    return db.exec(statement).all()
