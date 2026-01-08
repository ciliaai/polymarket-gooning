#!/usr/bin/env python3
"""Quick scan to show current hot markets and signals"""

import asyncio
import sys
sys.path.insert(0, ".")

from dotenv import load_dotenv
load_dotenv()

from polymarket_client import PolymarketClient, build_proxy_url
from edge_detector import EdgeDetector


async def scan():
    client = PolymarketClient(proxy_url=build_proxy_url())
    detector = EdgeDetector(min_odds_change=0.03, min_volume_usd=500)

    try:
        # Get markets
        markets = await client.get_markets(limit=30)
        print(f"=== HOT MARKETS ({len(markets)} found) ===\n")

        by_vol = sorted(markets, key=lambda m: m.volume_24h, reverse=True)[:7]
        for i, m in enumerate(by_vol, 1):
            q = m.question[:55] + "..." if len(m.question) > 55 else m.question
            vol = f"${m.volume_24h:,.0f}"
            print(f"{i}. {q}")
            print(f"   YES: {m.yes_price*100:.0f}c | NO: {m.no_price*100:.0f}c | Vol: {vol}")
            print()

        # Scan for signals (will build history over multiple runs)
        print("=== SCANNING FOR SIGNALS ===\n")
        edges = await detector.scan_all_markets(client, limit=30)

        if edges:
            print(f"Found {len(edges)} signals:\n")
            for e in edges[:5]:
                print(f"[{e.edge_type.upper()}] {e.market.question[:50]}...")
                print(f"  {e.direction} | Magnitude: {e.magnitude:.1f} | {e.confidence}")
                print(f"  {e.description}")
                print()
        else:
            print("No signals yet (run again to build price history)")
            print(f"Tracking {len(detector.price_history)} markets")

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(scan())
