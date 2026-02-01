from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.dependencies import get_db, get_current_active_user
from app.schemas.ig_post import InstagramPostCreate, InstagramPostRead, InstagramPostUpdate
from app.schemas.apify import ScrapePostsRequest, ScrapePostsResponse
from app.services import ig_post_service, ig_account_service
from app.services.apify_service import apify_service
from app.models.user import User


router = APIRouter(prefix="/instagram-posts", tags=["Instagram Posts"])


# Scraping Instagram posts data using Apify by username
@router.post("/scrape", response_model=ScrapePostsResponse)
def scrape_posts(
    request: ScrapePostsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Scrape Instagram posts data using Apify.
    
    This endpoint will:
    1. Use Apify to scrape posts for the given usernames
    2. The accounts must already exist in the database (scrape profiles first)
    3. Create new posts (skip existing ones)
    4. Return a summary of the operation
    """
    try:
        results = apify_service.scrape_and_save_posts(
            db=db,
            usernames=request.usernames,
            user_id=current_user.id,
            results_limit=request.results_limit,
            skip_pinned_posts=request.skip_pinned_posts,
            only_posts_newer_than=request.only_posts_newer_than,
        )
        
        return ScrapePostsResponse(
            success=results["success"],
            message=f"Scraped posts for {len(request.usernames)} accounts. Created: {results['posts_created']}, Skipped: {results['posts_skipped']}",
            data=results["data"],
            posts_created=results["posts_created"],
            errors=results["errors"] if results["errors"] else None
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error scraping posts: {str(e)}"
        )


@router.post("/{account_id}", response_model=InstagramPostRead, status_code=status.HTTP_201_CREATED)
def create_post(
    account_id: str,
    post: InstagramPostCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new Instagram post."""
    # Check if account exists and belongs to user
    db_account = ig_account_service.get_account_by_id(db, account_id=account_id)
    if db_account is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Instagram account not found"
        )
    if db_account.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to add posts to this account"
        )
    
    # Check if post URL already exists
    existing = ig_post_service.get_post_by_url(db, url=post.url)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Post with this URL already exists"
        )
    
    return ig_post_service.create_post(db=db, post=post, account_id=account_id)


@router.post("/{account_id}/bulk", response_model=List[InstagramPostRead], status_code=status.HTTP_201_CREATED)
def create_posts_bulk(
    account_id: str,
    posts: List[InstagramPostCreate],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create multiple Instagram posts at once."""
    # Check if account exists and belongs to user
    db_account = ig_account_service.get_account_by_id(db, account_id=account_id)
    if db_account is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Instagram account not found"
        )
    if db_account.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to add posts to this account"
        )
    
    return ig_post_service.create_posts_bulk(db=db, posts=posts, account_id=account_id)


@router.get("/account/{account_id}", response_model=List[InstagramPostRead])
def read_posts_by_account(
    account_id: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all Instagram posts for an account."""
    # Check if account exists and belongs to user
    db_account = ig_account_service.get_account_by_id(db, account_id=account_id)
    if db_account is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Instagram account not found"
        )
    if db_account.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this account"
        )
    
    posts = ig_post_service.get_posts_by_account(db, account_id=account_id, skip=skip, limit=limit)
    return posts


@router.get("/{post_id}", response_model=InstagramPostRead)
def read_post(
    post_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific Instagram post by ID."""
    db_post = ig_post_service.get_post_by_id(db, post_id=post_id)
    if db_post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Instagram post not found"
        )
    
    # Check ownership through account
    db_account = ig_account_service.get_account_by_id(db, account_id=db_post.instagram_account_id)
    if db_account.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this post"
        )
    
    return db_post


@router.put("/{post_id}", response_model=InstagramPostRead)
def update_post(
    post_id: str,
    post_update: InstagramPostUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update an Instagram post."""
    db_post = ig_post_service.get_post_by_id(db, post_id=post_id)
    if db_post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Instagram post not found"
        )
    
    # Check ownership through account
    db_account = ig_account_service.get_account_by_id(db, account_id=db_post.instagram_account_id)
    if db_account.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this post"
        )
    
    return ig_post_service.update_post(db, post_id=post_id, post_update=post_update)


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(
    post_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete an Instagram post."""
    db_post = ig_post_service.get_post_by_id(db, post_id=post_id)
    if db_post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Instagram post not found"
        )
    
    # Check ownership through account
    db_account = ig_account_service.get_account_by_id(db, account_id=db_post.instagram_account_id)
    if db_account.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this post"
        )
    
    ig_post_service.delete_post(db, post_id=post_id)