#!/usr/bin/env python3
"""Quick test to verify Twitter posting works"""

import asyncio
from dotenv import load_dotenv
load_dotenv()

from twitter_client import TwitterClient
from image_generator import GrokImageGenerator
from edge_detector import Edge
from polymarket_client import Market
from datetime import datetime


async def test_post():
    # Create a fake edge for testing
    fake_market = Market(
        condition_id="test123",
        question="Will Bitcoin reach $100k by end of 2025?",
        slug="bitcoin-100k-2025",
        yes_price=0.65,
        no_price=0.35,
        volume_24h=125000,
        liquidity=50000,
        end_date="2025-12-31",
        category="Crypto",
        yes_token_id="",
        no_token_id="",
    )

    fake_edge = Edge(
        market=fake_market,
        edge_type="odds_movement",
        description="big pump detected - YES moved +8c in recent checks",
        confidence="high",
        magnitude=15.0,
        direction="YES",
        detected_at=datetime.now(),
    )

    # Format test tweet
    tweet_text = """hourly alpha digest~

detected 3 signals

top pick: Will Bitcoin reach $100k by end of 2025?
YES @ 65c
signal: odds movement
risk: low

low risk: 1
med risk: 2

polymarket.com/event/bitcoin-100k-2025"""

    print("Initializing Twitter client...")
    twitter = TwitterClient()

    print("Initializing Grok image generator...")
    image_gen = GrokImageGenerator()

    print("Generating anime image...")
    import tempfile
    import os

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        image_success = await image_gen.generate_and_save(fake_edge, tmp_path)
        print(f"Image generated: {image_success}")

        if image_success:
            print("Posting tweet with image...")
            tweet_url = twitter.post_tweet(tweet_text, media_path=tmp_path)
        else:
            print("Posting tweet without image...")
            tweet_url = twitter.post_tweet(tweet_text)

        if tweet_url:
            print(f"\nSUCCESS! Posted: {tweet_url}")
        else:
            print("\nFailed to post tweet")

    finally:
        try:
            os.unlink(tmp_path)
        except:
            pass


if __name__ == "__main__":
    asyncio.run(test_post())
