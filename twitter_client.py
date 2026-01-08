"""
Twitter/X Client
Posts trading signals with images to @ciliaai
"""

import tweepy
import os
import tempfile
from typing import Optional
from edge_detector import Edge
from image_generator import GrokImageGenerator


class TwitterClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        access_token: Optional[str] = None,
        access_secret: Optional[str] = None,
    ):
        self.api_key = api_key or os.getenv("TWITTER_API_KEY")
        self.api_secret = api_secret or os.getenv("TWITTER_API_SECRET")
        self.access_token = access_token or os.getenv("TWITTER_ACCESS_TOKEN")
        self.access_secret = access_secret or os.getenv("TWITTER_ACCESS_SECRET")

        if not all([self.api_key, self.api_secret, self.access_token, self.access_secret]):
            raise ValueError("Twitter API credentials not fully configured")

        # V1.1 API for media upload
        auth = tweepy.OAuth1UserHandler(
            self.api_key, self.api_secret,
            self.access_token, self.access_secret
        )
        self.api_v1 = tweepy.API(auth)

        # V2 API for tweeting
        self.client = tweepy.Client(
            consumer_key=self.api_key,
            consumer_secret=self.api_secret,
            access_token=self.access_token,
            access_token_secret=self.access_secret,
        )

    def post_tweet(self, text: str, media_path: Optional[str] = None) -> Optional[str]:
        """Post a tweet with optional media attachment"""
        try:
            media_id = None

            if media_path:
                # Upload media using v1.1 API
                media = self.api_v1.media_upload(filename=media_path)
                media_id = media.media_id

            # Post tweet using v2 API
            if media_id:
                response = self.client.create_tweet(
                    text=text,
                    media_ids=[media_id]
                )
            else:
                response = self.client.create_tweet(text=text)

            if response.data:
                tweet_id = response.data["id"]
                return f"https://twitter.com/ciliaai/status/{tweet_id}"

            return None

        except tweepy.TweepyException as e:
            print(f"Twitter API error: {e}")
            return None

    async def post_edge_signal(
        self, edge: Edge, image_generator: GrokImageGenerator
    ) -> Optional[str]:
        """Generate image and post edge signal to Twitter"""

        # Generate tweet text
        tweet_text = edge.to_tweet_text()

        # Generate anime reaction image
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            image_success = await image_generator.generate_and_save(edge, tmp_path)

            if image_success:
                tweet_url = self.post_tweet(tweet_text, media_path=tmp_path)
            else:
                # Post without image if generation fails
                print("Image generation failed, posting text only")
                tweet_url = self.post_tweet(tweet_text)

            return tweet_url

        finally:
            # Clean up temp file
            try:
                os.unlink(tmp_path)
            except:
                pass


class DryRunTwitterClient:
    """Mock Twitter client for testing without actually posting"""

    def __init__(self):
        pass

    def post_tweet(self, text: str, media_path: Optional[str] = None) -> Optional[str]:
        print("\n" + "=" * 50)
        print("DRY RUN - Would post tweet:")
        print("-" * 50)
        print(text)
        if media_path:
            print(f"\n[With image: {media_path}]")
        print("=" * 50 + "\n")
        return "https://twitter.com/ciliaai/status/dry-run-123"

    async def post_edge_signal(
        self, edge: Edge, image_generator: GrokImageGenerator
    ) -> Optional[str]:
        tweet_text = edge.to_tweet_text()
        return self.post_tweet(tweet_text, media_path="[would generate anime image]")
