from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field


# ========== Request Schemas ==========

class ScrapeProfileRequest(BaseModel):
    """Request schema for scraping Instagram profile."""
    usernames: List[str] = Field(..., description="List of Instagram usernames to scrape")
    include_about_section: bool = Field(default=True, description="Whether to include the About section")
    
    class Config:
        json_schema_extra = {
            "example": {
                "usernames": ["instagram", "natgeo"],
                "include_about_section": True,
            }
        }


class ScrapePostsRequest(BaseModel):
    """Request schema for scraping Instagram posts."""
    usernames: List[str] = Field(..., description="List of Instagram usernames to scrape posts from")
    results_limit: int = Field(default=10, ge=1, le=100, description="Maximum number of posts to scrape per user")
    skip_pinned_posts: bool = Field(default=False, description="Whether to skip pinned posts")
    only_posts_newer_than: Optional[datetime] = Field(
        default=None,
        description="If set, only scrape posts newer than this timestamp (ISO 8601)",
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "usernames": ["instagram"],
                "results_limit": 10,
                "skip_pinned_posts": False,
                "only_posts_newer_than": None,
            }
        }


class ScrapeCommentsRequest(BaseModel):
    """Request schema for scraping Instagram comments."""
    post_urls: List[str] = Field(..., description="List of Instagram post URLs to scrape comments from")
    results_limit: int = Field(default=50, ge=1, le=500, description="Maximum number of comments to scrape per post")
    is_newest_comments: Optional[bool] = Field(
        default=None,
        description="If set, control ordering/filtering of comments as supported by the Apify actor",
    )
    include_nested_comments: Optional[bool] = Field(
        default=None,
        description="If set, include nested/thread replies as supported by the Apify actor",
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "post_urls": ["https://www.instagram.com/p/ABC123/"],
                "results_limit": 50,
                "is_newest_comments": None,
                "include_nested_comments": None,
            }
        }


# ========== Apify Raw Response Schemas ==========

class ApifyProfileData(BaseModel):
    """Raw profile data from Apify Instagram Profile Scraper."""
    id: Optional[str] = None
    username: str
    fullName: Optional[str] = Field(default=None, alias="fullName")
    full_name: Optional[str] = None
    biography: Optional[str] = None
    profilePicUrl: Optional[str] = Field(default=None, alias="profilePicUrl")
    profilePicUrlHD: Optional[str] = Field(default=None, alias="profilePicUrlHD")
    postsCount: Optional[int] = Field(default=0, alias="postsCount")
    followersCount: Optional[int] = Field(default=0, alias="followersCount")
    followsCount: Optional[int] = Field(default=0, alias="followsCount")
    private: bool = False
    verified: bool = False
    isBusinessAccount: bool = Field(default=False, alias="isBusinessAccount")
    
    class Config:
        populate_by_name = True
        
    @property
    def display_name(self) -> str:
        return self.fullName or self.full_name or self.username


class ApifyPostData(BaseModel):
    """Raw post data from Apify Instagram Post Scraper."""
    id: Optional[str] = None
    shortCode: Optional[str] = Field(default=None, alias="shortCode")
    caption: Optional[str] = None
    url: str
    displayUrl: Optional[str] = Field(default=None, alias="displayUrl")
    videoUrl: Optional[str] = Field(default=None, alias="videoUrl")
    likesCount: int = Field(default=0, alias="likesCount")
    commentsCount: int = Field(default=0, alias="commentsCount")
    ownerFullName: Optional[str] = Field(default=None, alias="ownerFullName")
    ownerUsername: str = Field(alias="ownerUsername")
    timestamp: Optional[datetime] = None
    firstComment: Optional[str] = Field(default=None, alias="firstComment")
    
    class Config:
        populate_by_name = True


class ApifyCommentData(BaseModel):
    """Raw comment data from Apify Instagram Comment Scraper."""
    id: str
    text: str
    ownerUsername: str = Field(alias="ownerUsername")
    ownerProfilePicUrl: Optional[str] = Field(default=None, alias="ownerProfilePicUrl")
    likesCount: int = Field(default=0, alias="likesCount")
    timestamp: Optional[datetime] = None
    repliesCount: int = Field(default=0, alias="repliesCount")
    
    class Config:
        populate_by_name = True


# ========== Response Schemas ==========

class ScrapeProfileResponse(BaseModel):
    """Response schema for profile scraping."""
    success: bool
    message: str
    data: Optional[List[dict]] = None
    accounts_created: int = 0
    errors: Optional[List[str]] = None


class ScrapePostsResponse(BaseModel):
    """Response schema for posts scraping."""
    success: bool
    message: str
    data: Optional[List[dict]] = None
    posts_created: int = 0
    errors: Optional[List[str]] = None


class ScrapeCommentsResponse(BaseModel):
    """Response schema for comments scraping."""
    success: bool
    message: str
    data: Optional[List[dict]] = None
    comments_created: int = 0
    errors: Optional[List[str]] = None


# ========== Actor Run Status ==========

class ActorRunStatus(BaseModel):
    """Schema for Apify Actor run status."""
    run_id: str
    status: str
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    dataset_id: Optional[str] = None
    items_count: int = 0
