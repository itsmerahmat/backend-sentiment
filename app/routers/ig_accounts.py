from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.dependencies import get_db, get_current_active_user
from app.schemas.ig_account import InstagramAccountCreate, InstagramAccountRead, InstagramAccountUpdate
from app.schemas.apify import ScrapeProfileRequest, ScrapeProfileResponse
from app.services import ig_account_service
from app.services.apify_service import apify_service
from app.models.user import User


router = APIRouter(prefix="/instagram-accounts", tags=["Instagram Accounts"])


# Scraping Instagram account data using Apify by username
@router.post("/scrape", response_model=ScrapeProfileResponse)
def scrape_account(
    request: ScrapeProfileRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Scrape Instagram account data using Apify.
    
    This endpoint will:
    1. Use Apify to scrape profile data for the given usernames
    2. Create new accounts or update existing ones
    3. Return a summary of the operation
    """
    try:
        results = apify_service.scrape_and_save_profiles(
            db=db,
            usernames=request.usernames,
            user_id=current_user.id,
            include_about_section=request.include_about_section,
        )
        
        return ScrapeProfileResponse(
            success=results["success"],
            message=f"Scraped {len(request.usernames)} profiles. Created: {results['accounts_created']}, Updated: {results['accounts_updated']}",
            data=results["data"],
            accounts_created=results["accounts_created"],
            errors=results["errors"] if results["errors"] else None
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error scraping profiles: {str(e)}"
        )


@router.post("/", response_model=InstagramAccountRead, status_code=status.HTTP_201_CREATED)
def create_account(
    account: InstagramAccountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new Instagram account."""
    # Check if username already exists
    existing = ig_account_service.get_account_by_username(db, username=account.username)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Instagram account with this username already exists"
        )
    
    return ig_account_service.create_account(db=db, account=account, user_id=current_user.id)


@router.get("/", response_model=List[InstagramAccountRead])
def read_accounts(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all Instagram accounts for current user."""
    accounts = ig_account_service.get_accounts_by_user(db, user_id=current_user.id, skip=skip, limit=limit)
    return accounts


@router.get("/{account_id}", response_model=InstagramAccountRead)
def read_account(
    account_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific Instagram account by ID."""
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
    return db_account


@router.get("/username/{username}", response_model=InstagramAccountRead)
def read_account_by_username(
    username: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get an Instagram account by username."""
    db_account = ig_account_service.get_account_by_username(db, username=username)
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
    return db_account


@router.put("/{account_id}", response_model=InstagramAccountRead)
def update_account(
    account_id: str,
    account_update: InstagramAccountUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update an Instagram account."""
    db_account = ig_account_service.get_account_by_id(db, account_id=account_id)
    if db_account is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Instagram account not found"
        )
    if db_account.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this account"
        )
    
    return ig_account_service.update_account(db, account_id=account_id, account_update=account_update)


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(
    account_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete an Instagram account."""
    db_account = ig_account_service.get_account_by_id(db, account_id=account_id)
    if db_account is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Instagram account not found"
        )
    if db_account.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this account"
        )
    
    ig_account_service.delete_account(db, account_id=account_id)