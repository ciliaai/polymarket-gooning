"""
Twitter/X Integration

Handles posting signals and digests to Twitter.
Includes rate limiting and media upload support.
"""

import tweepy
import os
import tempfile
from typing import Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class TweetResult:
    success: bool
    tweet_id: Optional[str]
    url: Optional[str]
    error: Optional[str]
    posted_at: datetime


class TwitterPoster:
    """
    Twitter posting client with media upload support.

    Uses Twitter API v2 for posting and v1.1 for media upload.
    Implements rate limiting and error handling.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        access_token: Optional[str] = None,
        access_secret: Optional[str] = None,
        account_name: str = "ciliaai",
    ):
        self.api_key = api_key or os.getenv("TWITTER_API_KEY")
        self.api_secret = api_secret or os.getenv("TWITTER_API_SECRET")
        self.access_token = access_token or os.getenv("TWITTER_ACCESS_TOKEN")
        self.access_secret = access_secret or os.getenv("TWITTER_ACCESS_SECRET")
        self.account_name = account_name

        self._posts_today = 0
        self._last_post_time: Optional[datetime] = None

        if not all([self.api_key, self.api_secret, self.access_token, self.access_secret]):
            raise ValueError("Twitter API credentials not configured")

        # Initialize clients
        auth = tweepy.OAuth1UserHandler(
            self.api_key,
            self.api_secret,
            self.access_token,
            self.access_secret,
        )
        self.api_v1 = tweepy.API(auth)

        self.client_v2 = tweepy.Client(
            consumer_key=self.api_key,
            consumer_secret=self.api_secret,
            access_token=self.access_token,
            access_token_secret=self.access_secret,
        )

    def upload_media(self, file_path: str) -> Optional[str]:
        """Upload media file and return media ID"""
        try:
            media = self.api_v1.media_upload(filename=file_path)
            return str(media.media_id)
        except tweepy.TweepyException as e:
            print(f"Media upload error: {e}")
            return None

    def post(
        self,
        text: str,
        media_path: Optional[str] = None,
    ) -> TweetResult:
        """Post a tweet with optional media"""
        try:
            media_ids = None

            if media_path and os.path.exists(media_path):
                media_id = self.upload_media(media_path)
                if media_id:
                    media_ids = [media_id]

            if media_ids:
                response = self.client_v2.create_tweet(
                    text=text,
                    media_ids=media_ids,
                )
            else:
                response = self.client_v2.create_tweet(text=text)

            if response.data:
                tweet_id = response.data["id"]
                self._posts_today += 1
                self._last_post_time = datetime.now()

                return TweetResult(
                    success=True,
                    tweet_id=tweet_id,
                    url=f"https://twitter.com/{self.account_name}/status/{tweet_id}",
                    error=None,
                    posted_at=datetime.now(),
                )

            return TweetResult(
                success=False,
                tweet_id=None,
                url=None,
                error="No response data",
                posted_at=datetime.now(),
            )

        except tweepy.TweepyException as e:
            return TweetResult(
                success=False,
                tweet_id=None,
                url=None,
                error=str(e),
                posted_at=datetime.now(),
            )

    def can_post(self, daily_limit: int = 17) -> bool:
        """Check if we can post (rate limit check)"""
        # Reset counter if new day
        if self._last_post_time:
            if self._last_post_time.date() != datetime.now().date():
                self._posts_today = 0

        return self._posts_today < daily_limit

    def get_stats(self) -> dict:
        """Get posting statistics"""
        return {
            "posts_today": self._posts_today,
            "last_post": self._last_post_time,
            "can_post": self.can_post(),
        }


class DryRunPoster:
    """Mock poster for testing"""

    def __init__(self, account_name: str = "ciliaai"):
        self.account_name = account_name
        self._posts = []

    def post(
        self,
        text: str,
        media_path: Optional[str] = None,
    ) -> TweetResult:
        print("\n" + "=" * 50)
        print("DRY RUN - Would post:")
        print("-" * 50)
        print(text)
        if media_path:
            print(f"\n[With image: {media_path}]")
        print("=" * 50 + "\n")

        self._posts.append({
            "text": text,
            "media": media_path,
            "time": datetime.now(),
        })

        return TweetResult(
            success=True,
            tweet_id="dry-run-123",
            url=f"https://twitter.com/{self.account_name}/status/dry-run-123",
            error=None,
            posted_at=datetime.now(),
        )

    def can_post(self, daily_limit: int = 17) -> bool:
        return True

    def get_stats(self) -> dict:
        return {
            "posts_today": len(self._posts),
            "last_post": self._posts[-1]["time"] if self._posts else None,
            "can_post": True,
            "mode": "dry_run",
        }
