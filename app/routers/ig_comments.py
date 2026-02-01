from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.dependencies import get_db, get_current_active_user
from app.schemas.ig_comment import InstagramCommentCreate, InstagramCommentRead, InstagramCommentUpdate
from app.schemas.apify import ScrapeCommentsRequest, ScrapeCommentsResponse
from app.services import ig_comment_service, ig_post_service, ig_account_service
from app.services.apify_service import apify_service
from app.models.user import User


router = APIRouter(prefix="/instagram-comments", tags=["Instagram Comments"])


# Scraping Instagram comments data using Apify by url
@router.post("/scrape", response_model=ScrapeCommentsResponse)
def scrape_comments(
    request: ScrapeCommentsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Scrape Instagram comments data using Apify.
    
    This endpoint will:
    1. Use Apify to scrape comments for the given post URLs
    2. The posts must already exist in the database (scrape posts first)
    3. Create new comments (skip existing ones)
    4. Return a summary of the operation
    """
    try:
        results = apify_service.scrape_and_save_comments(
            db=db,
            post_urls=request.post_urls,
            user_id=current_user.id,
            results_limit=request.results_limit,
            is_newest_comments=request.is_newest_comments,
            include_nested_comments=request.include_nested_comments,
        )
        
        return ScrapeCommentsResponse(
            success=results["success"],
            message=f"Scraped comments for {len(request.post_urls)} posts. Created: {results['comments_created']}, Skipped: {results['comments_skipped']}",
            data=results["data"],
            comments_created=results["comments_created"],
            errors=results["errors"] if results["errors"] else None
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error scraping comments: {str(e)}"
        )


@router.post("/{post_id}", response_model=InstagramCommentRead, status_code=status.HTTP_201_CREATED)
def create_comment(
    post_id: str,
    comment: InstagramCommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new Instagram comment."""
    # Check if post exists and user has access
    db_post = ig_post_service.get_post_by_id(db, post_id=post_id)
    if db_post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Instagram post not found"
        )
    
    db_account = ig_account_service.get_account_by_id(db, account_id=db_post.instagram_account_id)
    if db_account.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to add comments to this post"
        )
    
    # Check if comment_id already exists
    existing = ig_comment_service.get_comment_by_comment_id(db, comment_id=comment.comment_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Comment with this ID already exists"
        )
    
    return ig_comment_service.create_comment(db=db, comment=comment, post_id=post_id)


@router.post("/{post_id}/bulk", response_model=List[InstagramCommentRead], status_code=status.HTTP_201_CREATED)
def create_comments_bulk(
    post_id: str,
    comments: List[InstagramCommentCreate],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create multiple Instagram comments at once."""
    # Check if post exists and user has access
    db_post = ig_post_service.get_post_by_id(db, post_id=post_id)
    if db_post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Instagram post not found"
        )
    
    db_account = ig_account_service.get_account_by_id(db, account_id=db_post.instagram_account_id)
    if db_account.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to add comments to this post"
        )
    
    return ig_comment_service.create_comments_bulk(db=db, comments=comments, post_id=post_id)


@router.get("/post/{post_id}", response_model=List[InstagramCommentRead])
def read_comments_by_post(
    post_id: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all Instagram comments for a post."""
    # Check if post exists and user has access
    db_post = ig_post_service.get_post_by_id(db, post_id=post_id)
    if db_post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Instagram post not found"
        )
    
    db_account = ig_account_service.get_account_by_id(db, account_id=db_post.instagram_account_id)
    if db_account.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this post's comments"
        )
    
    comments = ig_comment_service.get_comments_by_post(db, post_id=post_id, skip=skip, limit=limit)
    return comments


@router.get("/{comment_id}", response_model=InstagramCommentRead)
def read_comment(
    comment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific Instagram comment by ID."""
    db_comment = ig_comment_service.get_comment_by_id(db, comment_id=comment_id)
    if db_comment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Instagram comment not found"
        )
    
    # Check ownership through post -> account
    db_post = ig_post_service.get_post_by_id(db, post_id=db_comment.instagram_post_id)
    db_account = ig_account_service.get_account_by_id(db, account_id=db_post.instagram_account_id)
    if db_account.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this comment"
        )
    
    return db_comment


@router.put("/{comment_id}", response_model=InstagramCommentRead)
def update_comment(
    comment_id: str,
    comment_update: InstagramCommentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update an Instagram comment (mainly for sentiment analysis results)."""
    db_comment = ig_comment_service.get_comment_by_id(db, comment_id=comment_id)
    if db_comment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Instagram comment not found"
        )
    
    # Check ownership through post -> account
    db_post = ig_post_service.get_post_by_id(db, post_id=db_comment.instagram_post_id)
    db_account = ig_account_service.get_account_by_id(db, account_id=db_post.instagram_account_id)
    if db_account.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this comment"
        )
    
    return ig_comment_service.update_comment(db, comment_id=comment_id, comment_update=comment_update)


@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(
    comment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete an Instagram comment."""
    db_comment = ig_comment_service.get_comment_by_id(db, comment_id=comment_id)
    if db_comment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Instagram comment not found"
        )
    
    # Check ownership through post -> account
    db_post = ig_post_service.get_post_by_id(db, post_id=db_comment.instagram_post_id)
    db_account = ig_account_service.get_account_by_id(db, account_id=db_post.instagram_account_id)
    if db_account.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this comment"
        )
    
    ig_comment_service.delete_comment(db, comment_id=comment_id)