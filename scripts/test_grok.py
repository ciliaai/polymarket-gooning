#!/usr/bin/env python3
"""Test Grok image generation"""

import asyncio
import httpx
import os
from dotenv import load_dotenv

load_dotenv()


async def test_grok_image():
    api_key = os.getenv("GROK_API_KEY")
    print(f"API Key: {api_key[:20]}...")

    # Try the documented endpoint
    url = "https://api.x.ai/v1/images/generations"

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            print(f"\nCalling: {url}")
            resp = await client.post(
                url,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "grok-2-image",
                    "prompt": "cute anime girl with pink hair, kawaii style, excited expression, trading charts in background",
                    "n": 1,
                },
            )

            print(f"Status: {resp.status_code}")
            print(f"Response: {resp.text[:500]}")

            if resp.status_code == 200:
                data = resp.json()
                print("\nSUCCESS!")
                print(f"Data keys: {data.keys()}")

                if data.get("data"):
                    item = data["data"][0]
                    print(f"Item keys: {item.keys()}")

                    # Check for URL or b64
                    if "url" in item:
                        print(f"Image URL: {item['url']}")
                    if "b64_json" in item:
                        print(f"Got base64 image, length: {len(item['b64_json'])}")

        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(test_grok_image())
