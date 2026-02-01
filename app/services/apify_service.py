from typing import List, Optional, Dict, Any
from datetime import datetime

from apify_client import ApifyClient
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.core.config import settings
from app.models.ig_account import InstagramAccount
from app.models.ig_comment import InstagramComment
from app.models.ig_post import InstagramPost
from app.schemas.ig_account import InstagramAccountCreate
from app.schemas.ig_post import InstagramPostCreate
from app.schemas.ig_comment import InstagramCommentCreate
from app.services import ig_account_service


class ApifyService:
    """Service for interacting with Apify actors."""
    
    def __init__(self):
        self.client = ApifyClient(settings.APIFY_TOKEN)
        self.profile_scraper_id = settings.APIFY_INSTAGRAM_PROFILE_SCRAPER_ID
        self.post_scraper_id = settings.APIFY_INSTAGRAM_POST_SCRAPER_ID
        self.comment_scraper_id = settings.APIFY_INSTAGRAM_COMMENTS_SCRAPER_ID
    
    def scrape_profiles(
        self,
        usernames: List[str],
        include_about_section: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Scrape Instagram profiles using Apify actor.
        
        Args:
            usernames: List of Instagram usernames to scrape
            
        Returns:
            List of profile data dictionaries
        """
        run_input = {
            "usernames": usernames,
            "includeAboutSection": include_about_section,
        }
        
        # Run the actor and wait for it to finish
        run = self.client.actor(self.profile_scraper_id).call(run_input=run_input)
        
        # Fetch results from the run's dataset
        items = list(self.client.dataset(run["defaultDatasetId"]).iterate_items())
        
        return items
    
    def scrape_posts(
        self,
        usernames: List[str],
        results_limit: int = 10,
        skip_pinned_posts: bool = False,
        only_posts_newer_than: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """
        Scrape Instagram posts using Apify actor.
        
        Args:
            usernames: List of Instagram usernames to scrape posts from
            results_limit: Maximum number of posts per user
            
        Returns:
            List of post data dictionaries
        """
        run_input = {
            "username": usernames,
            "resultsLimit": results_limit,
            "skipPinnedPosts": skip_pinned_posts,
        }

        if only_posts_newer_than is not None:
            run_input["onlyPostsNewerThan"] = only_posts_newer_than.isoformat()
        
        # Run the actor and wait for it to finish
        run = self.client.actor(self.post_scraper_id).call(run_input=run_input)
        
        # Fetch results from the run's dataset
        items = list(self.client.dataset(run["defaultDatasetId"]).iterate_items())
        
        return items
    
    def scrape_comments(
        self,
        post_urls: List[str],
        results_limit: int = 50,
        is_newest_comments: Optional[bool] = None,
        include_nested_comments: Optional[bool] = None,
    ) -> List[Dict[str, Any]]:
        """
        Scrape Instagram comments using Apify actor.
        
        Args:
            post_urls: List of Instagram post URLs to scrape comments from
            results_limit: Maximum number of comments per post
            
        Returns:
            List of comment data dictionaries
        """
        run_input = {
            "directUrls": post_urls,
            "resultsLimit": results_limit,
        }

        if is_newest_comments is not None:
            run_input["isNewestComments"] = is_newest_comments
        if include_nested_comments is not None:
            run_input["includeNestedComments"] = include_nested_comments
        
        # Run the actor and wait for it to finish
        run = self.client.actor(self.comment_scraper_id).call(run_input=run_input)
        
        # Fetch results from the run's dataset
        items = list(self.client.dataset(run["defaultDatasetId"]).iterate_items())
        
        return items
    
    def parse_profile_data(self, raw_data: Dict[str, Any]) -> InstagramAccountCreate:
        """
        Parse raw Apify profile data to InstagramAccountCreate schema.
        
        Args:
            raw_data: Raw profile data from Apify
            
        Returns:
            InstagramAccountCreate schema
        """
        return InstagramAccountCreate(
            full_name=raw_data.get("fullName") or raw_data.get("full_name") or raw_data.get("username", ""),
            username=raw_data.get("username", ""),
            profile_pic_url=raw_data.get("profilePicUrlHD") or raw_data.get("profilePicUrl") or "",
            posts_count=raw_data.get("postsCount", 0),
            followers_count=raw_data.get("followersCount", 0),
            follows_count=raw_data.get("followsCount", 0),
            biography=raw_data.get("biography"),
            private=raw_data.get("private", False),
            verified=raw_data.get("verified", False),
            is_business_account=raw_data.get("isBusinessAccount", False),
        )
    
    def parse_post_data(self, raw_data: Dict[str, Any]) -> InstagramPostCreate:
        """
        Parse raw Apify post data to InstagramPostCreate schema.
        
        Args:
            raw_data: Raw post data from Apify
            
        Returns:
            InstagramPostCreate schema
        """
        # Parse timestamp
        timestamp = raw_data.get("timestamp")
        if isinstance(timestamp, str):
            try:
                timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            except Exception:
                timestamp = datetime.utcnow()
        elif timestamp is None:
            timestamp = datetime.utcnow()
            
        return InstagramPostCreate(
            caption=raw_data.get("caption"),
            owner_full_name=raw_data.get("ownerFullName") or raw_data.get("ownerUsername", ""),
            owner_username=raw_data.get("ownerUsername", ""),
            display_url=raw_data.get("displayUrl"),
            video_url=raw_data.get("videoUrl"),
            url=raw_data.get("url", ""),
            likes_count=raw_data.get("likesCount", 0),
            comments_count=raw_data.get("commentsCount", 0),
            first_comment=raw_data.get("firstComment"),
            timestamp=timestamp,
        )
    
    def parse_comment_data(self, raw_data: Dict[str, Any]) -> InstagramCommentCreate:
        """
        Parse raw Apify comment data to InstagramCommentCreate schema.
        
        Args:
            raw_data: Raw comment data from Apify
            
        Returns:
            InstagramCommentCreate schema
        """
        # Parse timestamp
        timestamp = raw_data.get("timestamp")
        if isinstance(timestamp, str):
            try:
                timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            except Exception:
                timestamp = datetime.utcnow()
        elif timestamp is None:
            timestamp = datetime.utcnow()
            
        return InstagramCommentCreate(
            comment_id=raw_data.get("id", ""),
            text=raw_data.get("text", ""),
            owner_username=raw_data.get("ownerUsername", ""),
            likes_count=raw_data.get("likesCount", 0),
            timestamp=timestamp,
        )
    
    def scrape_and_save_profiles(
        self, 
        db: Session, 
        usernames: List[str], 
        user_id: str,
        include_about_section: bool = False,
    ) -> Dict[str, Any]:
        """
        Scrape Instagram profiles and save to database.
        
        Args:
            db: Database session
            usernames: List of usernames to scrape
            user_id: User ID to associate accounts with
            
        Returns:
            Dictionary with results summary
        """
        results = {
            "success": True,
            "accounts_created": 0,
            "accounts_updated": 0,
            "errors": [],
            "data": []
        }
        
        try:
            raw_profiles = self.scrape_profiles(
                usernames=usernames,
                include_about_section=include_about_section,
            )
            
            for raw_profile in raw_profiles:
                try:
                    account_data = self.parse_profile_data(raw_profile)
                    
                    # Check if account already exists
                    existing = ig_account_service.get_account_by_username(db, username=account_data.username)
                    
                    if existing:
                        # Update existing account
                        from app.schemas.ig_account import InstagramAccountUpdate
                        update_data = InstagramAccountUpdate(
                            full_name=account_data.full_name,
                            profile_pic_url=account_data.profile_pic_url,
                            posts_count=account_data.posts_count,
                            followers_count=account_data.followers_count,
                            follows_count=account_data.follows_count,
                            biography=account_data.biography,
                            private=account_data.private,
                            verified=account_data.verified,
                            is_business_account=account_data.is_business_account,
                        )
                        updated = ig_account_service.update_account(db, account_id=existing.id, account_update=update_data)
                        results["accounts_updated"] += 1
                        results["data"].append({"id": updated.id, "username": updated.username, "action": "updated"})
                    else:
                        # Create new account
                        created = ig_account_service.create_account(db, account=account_data, user_id=user_id)
                        results["accounts_created"] += 1
                        results["data"].append({"id": created.id, "username": created.username, "action": "created"})
                        
                except Exception as e:
                    results["errors"].append(f"Error processing profile {raw_profile.get('username', 'unknown')}: {str(e)}")
                    
        except Exception as e:
            results["success"] = False
            results["errors"].append(f"Apify scraping error: {str(e)}")
            
        return results
    
    def scrape_and_save_posts(
        self, 
        db: Session, 
        usernames: List[str],
        user_id: str,
        results_limit: int = 10,
        skip_pinned_posts: bool = False,
        only_posts_newer_than: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Scrape Instagram posts and save to database.
        
        Args:
            db: Database session
            usernames: List of usernames to scrape posts from
            user_id: User ID for authorization check
            results_limit: Maximum posts per user
            
        Returns:
            Dictionary with results summary
        """
        results = {
            "success": True,
            "posts_created": 0,
            "posts_skipped": 0,
            "errors": [],
            "data": []
        }
        
        try:
            raw_posts = self.scrape_posts(
                usernames=usernames,
                results_limit=results_limit,
                skip_pinned_posts=skip_pinned_posts,
                only_posts_newer_than=only_posts_newer_than,
            )

            requested_usernames = [u.lstrip("@").strip() for u in usernames if u and u.strip()]
            requested_usernames_set = set(requested_usernames)

            parsed_posts: List[InstagramPostCreate] = []
            for raw_post in raw_posts:
                try:
                    post_data = self.parse_post_data(raw_post)

                    # Handle collab posts: Apify can return an ownerUsername that isn't the
                    # requested account (e.g., collaborator). In that case, prefer the source
                    # username we requested so we can associate the post to an existing account.
                    raw_source_username = (
                        raw_post.get("username")
                        or raw_post.get("inputUsername")
                        or raw_post.get("input_username")
                    )
                    if isinstance(raw_source_username, str):
                        raw_source_username = raw_source_username.lstrip("@").strip()
                    else:
                        raw_source_username = None

                    current_owner = (post_data.owner_username or "").lstrip("@").strip()
                    effective_owner: Optional[str] = None

                    if raw_source_username and raw_source_username in requested_usernames_set:
                        effective_owner = raw_source_username
                    elif current_owner in requested_usernames_set:
                        effective_owner = current_owner
                    elif len(requested_usernames) == 1:
                        effective_owner = requested_usernames[0]

                    if effective_owner and effective_owner != post_data.owner_username:
                        post_data.owner_username = effective_owner

                    parsed_posts.append(post_data)
                except Exception as e:
                    results["errors"].append(f"Error processing post: {str(e)}")

            if not parsed_posts:
                return results

            owner_usernames = {p.owner_username for p in parsed_posts if p.owner_username}
            if not owner_usernames:
                results["errors"].append("No owner usernames found in scraped posts")
                return results

            accounts = db.exec(
                select(InstagramAccount).where(InstagramAccount.username.in_(owner_usernames))
            ).all()
            accounts_by_username = {a.username: a for a in accounts}

            candidates: List[tuple[InstagramPostCreate, InstagramAccount]] = []
            for post_data in parsed_posts:
                account = accounts_by_username.get(post_data.owner_username)
                if not account:
                    results["errors"].append(
                        f"Account @{post_data.owner_username} not found. Please scrape profile first."
                    )
                    continue
                if account.user_id != user_id:
                    results["errors"].append(
                        f"Not authorized to add posts for @{post_data.owner_username}"
                    )
                    continue
                if not post_data.url:
                    results["errors"].append(f"Post for @{post_data.owner_username} missing URL")
                    continue
                candidates.append((post_data, account))

            if not candidates:
                return results

            candidate_urls = {p.url for p, _ in candidates}
            existing_urls = set(
                db.exec(
                    select(InstagramPost.url).where(InstagramPost.url.in_(candidate_urls))
                ).all()
            )

            new_posts: List[InstagramPost] = []
            for post_data, account in candidates:
                if post_data.url in existing_urls:
                    results["posts_skipped"] += 1
                    continue
                new_posts.append(
                    InstagramPost(
                        instagram_account_id=account.id,
                        caption=post_data.caption,
                        owner_full_name=account.full_name,
                        owner_username=post_data.owner_username,
                        display_url=post_data.display_url,
                        video_url=post_data.video_url,
                        url=post_data.url,
                        likes_count=post_data.likes_count,
                        comments_count=post_data.comments_count,
                        first_comment=post_data.first_comment,
                        timestamp=post_data.timestamp,
                    )
                )

            if not new_posts:
                return results

            # Capture payload before commit to avoid N+1 refresh queries after commit
            posts_data_before_commit = [
                {"id": p.id, "url": p.url, "account_username": p.owner_username}
                for p in new_posts
            ]

            def _commit_posts_batch() -> None:
                db.add_all(new_posts)
                db.commit()

            try:
                _commit_posts_batch()
            except IntegrityError:
                db.rollback()
                # Retry once after re-checking existing URLs (handles races)
                existing_urls_retry = set(
                    db.exec(
                        select(InstagramPost.url).where(InstagramPost.url.in_(candidate_urls))
                    ).all()
                )
                new_posts[:] = [p for p in new_posts if p.url not in existing_urls_retry]
                posts_data_before_commit[:] = [
                    {"id": p.id, "url": p.url, "account_username": p.owner_username}
                    for p in new_posts
                ]
                if new_posts:
                    _commit_posts_batch()

            results["posts_created"] += len(new_posts)
            results["data"].extend(posts_data_before_commit)

        except Exception as e:
            results["success"] = False
            results["errors"].append(f"Apify scraping error: {str(e)}")

        return results
    
    def scrape_and_save_comments(
        self, 
        db: Session, 
        post_urls: List[str],
        user_id: str,
        results_limit: int = 50,
        is_newest_comments: Optional[bool] = None,
        include_nested_comments: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        Scrape Instagram comments and save to database.
        
        Args:
            db: Database session
            post_urls: List of post URLs to scrape comments from
            user_id: User ID for authorization check
            results_limit: Maximum comments per post
            
        Returns:
            Dictionary with results summary
        """
        results = {
            "success": True,
            "comments_created": 0,
            "comments_skipped": 0,
            "errors": [],
            "data": []
        }
        
        try:
            raw_comments = self.scrape_comments(
                post_urls=post_urls,
                results_limit=results_limit,
                is_newest_comments=is_newest_comments,
                include_nested_comments=include_nested_comments,
            )

            parsed_comments: List[tuple[InstagramCommentCreate, str]] = []
            for raw_comment in raw_comments:
                try:
                    comment_data = self.parse_comment_data(raw_comment)
                    post_url = raw_comment.get("postUrl") or raw_comment.get("inputUrl")
                    if not post_url:
                        results["errors"].append("Comment missing post URL reference")
                        continue
                    if not comment_data.comment_id:
                        results["errors"].append(f"Comment missing comment_id for post: {post_url}")
                        continue
                    parsed_comments.append((comment_data, post_url))
                except Exception as e:
                    results["errors"].append(f"Error processing comment: {str(e)}")

            if not parsed_comments:
                return results

            comment_post_urls = {post_url for _, post_url in parsed_comments}
            posts = db.exec(
                select(InstagramPost).where(InstagramPost.url.in_(comment_post_urls))
            ).all()
            posts_by_url = {p.url: p for p in posts}

            account_ids = {p.instagram_account_id for p in posts}
            accounts = db.exec(
                select(InstagramAccount).where(InstagramAccount.id.in_(account_ids))
            ).all()
            accounts_by_id = {a.id: a for a in accounts}

            candidates: List[tuple[InstagramCommentCreate, InstagramPost, str]] = []
            for comment_data, post_url in parsed_comments:
                post = posts_by_url.get(post_url)
                if not post:
                    results["errors"].append(f"Post not found for URL: {post_url}")
                    continue
                account = accounts_by_id.get(post.instagram_account_id)
                if not account:
                    results["errors"].append(f"Account not found for post: {post_url}")
                    continue
                if account.user_id != user_id:
                    results["errors"].append(f"Not authorized to add comments to post: {post_url}")
                    continue
                candidates.append((comment_data, post, post_url))

            if not candidates:
                return results

            candidate_comment_ids = {c.comment_id for c, _, _ in candidates}
            existing_comment_ids = set(
                db.exec(
                    select(InstagramComment.comment_id).where(
                        InstagramComment.comment_id.in_(candidate_comment_ids)
                    )
                ).all()
            )

            new_comments: List[InstagramComment] = []
            for comment_data, post, post_url in candidates:
                if comment_data.comment_id in existing_comment_ids:
                    results["comments_skipped"] += 1
                    continue
                new_comments.append(
                    InstagramComment(
                        instagram_post_id=post.id,
                        comment_id=comment_data.comment_id,
                        text=comment_data.text,
                        owner_username=comment_data.owner_username,
                        likes_count=comment_data.likes_count,
                        timestamp=comment_data.timestamp,
                    )
                )

            if not new_comments:
                return results

            # Build post_url lookup for result payload
            post_url_by_post_id = {p.id: url for url, p in posts_by_url.items()}

            # Capture payload before commit to avoid N+1 refresh queries after commit
            comments_data_before_commit = [
                {
                    "id": c.id,
                    "comment_id": c.comment_id,
                    "post_url": post_url_by_post_id.get(c.instagram_post_id),
                }
                for c in new_comments
            ]

            def _commit_comments_batch() -> None:
                db.add_all(new_comments)
                db.commit()

            try:
                _commit_comments_batch()
            except IntegrityError:
                db.rollback()
                existing_comment_ids_retry = set(
                    db.exec(
                        select(InstagramComment.comment_id).where(
                            InstagramComment.comment_id.in_(candidate_comment_ids)
                        )
                    ).all()
                )
                new_comments[:] = [c for c in new_comments if c.comment_id not in existing_comment_ids_retry]
                comments_data_before_commit[:] = [
                    {
                        "id": c.id,
                        "comment_id": c.comment_id,
                        "post_url": post_url_by_post_id.get(c.instagram_post_id),
                    }
                    for c in new_comments
                ]
                if new_comments:
                    _commit_comments_batch()

            results["comments_created"] += len(new_comments)
            results["data"].extend(comments_data_before_commit)

        except Exception as e:
            results["success"] = False
            results["errors"].append(f"Apify scraping error: {str(e)}")

        return results


# Singleton instance
apify_service = ApifyService()
