#!/usr/bin/env python3
import asyncio
import httpx

async def debug():
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            "https://gamma-api.polymarket.com/markets",
            params={"limit": 3, "active": "true", "closed": "false"}
        )
        print(f"Status: {resp.status_code}")
        data = resp.json()
        print(f"Got {len(data)} items")

        for m in data:
            print(f"\nQuestion: {m.get('question', 'N/A')[:50]}")
            print(f"  outcomePrices type: {type(m.get('outcomePrices'))}")
            print(f"  outcomePrices value: {m.get('outcomePrices')}")
            print(f"  volume24hr: {m.get('volume24hr')}")
            print(f"  clobTokenIds: {m.get('clobTokenIds')[:1] if m.get('clobTokenIds') else None}...")

asyncio.run(debug())
