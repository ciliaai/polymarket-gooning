#!/usr/bin/env python3
"""
Test Twitter posting without full bot.
Useful for debugging 403 errors.
"""

import sys
sys.path.insert(0, ".")

from dotenv import load_dotenv
load_dotenv()

import os
import tweepy


def test_auth():
    """Test Twitter authentication"""
    print("Testing Twitter Authentication")
    print("=" * 50)

    api_key = os.getenv("TWITTER_API_KEY")
    api_secret = os.getenv("TWITTER_API_SECRET")
    access_token = os.getenv("TWITTER_ACCESS_TOKEN")
    access_secret = os.getenv("TWITTER_ACCESS_SECRET")

    print(f"API Key: {api_key[:10]}..." if api_key else "API Key: MISSING")
    print(f"API Secret: {api_secret[:10]}..." if api_secret else "API Secret: MISSING")
    print(f"Access Token: {access_token[:10]}..." if access_token else "Access Token: MISSING")
    print(f"Access Secret: {access_secret[:10]}..." if access_secret else "Access Secret: MISSING")

    if not all([api_key, api_secret, access_token, access_secret]):
        print("\nERROR: Missing credentials!")
        return

    print("\n" + "-" * 50)
    print("Attempting to authenticate...")

    try:
        # Test v1.1 auth
        auth = tweepy.OAuth1UserHandler(
            api_key, api_secret,
            access_token, access_secret
        )
        api_v1 = tweepy.API(auth)

        # Verify credentials
        user = api_v1.verify_credentials()
        print(f"v1.1 Auth SUCCESS: @{user.screen_name}")

    except tweepy.TweepyException as e:
        print(f"v1.1 Auth FAILED: {e}")

    try:
        # Test v2 client
        client_v2 = tweepy.Client(
            consumer_key=api_key,
            consumer_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_secret,
        )

        # Get authenticated user
        me = client_v2.get_me()
        if me.data:
            print(f"v2 Auth SUCCESS: @{me.data.username}")
        else:
            print("v2 Auth: No user data returned")

    except tweepy.TweepyException as e:
        print(f"v2 Auth FAILED: {e}")

    print("\n" + "-" * 50)
    print("Testing write permission...")

    try:
        # Try to post (will fail without write permissions)
        response = client_v2.create_tweet(text="test - please ignore (will delete)")
        if response.data:
            tweet_id = response.data["id"]
            print(f"POST SUCCESS: Tweet ID {tweet_id}")

            # Delete test tweet
            client_v2.delete_tweet(tweet_id)
            print("Test tweet deleted")
        else:
            print("POST FAILED: No response data")

    except tweepy.Forbidden as e:
        print(f"POST FAILED (403 Forbidden): {e}")
        print("\nThis usually means:")
        print("1. App permissions are not set to 'Read and Write'")
        print("2. You need to regenerate tokens AFTER changing permissions")
        print("3. Go to developer.x.com → Your App → Settings → User auth → Read and Write")

    except tweepy.TweepyException as e:
        print(f"POST FAILED: {e}")


if __name__ == "__main__":
    test_auth()
