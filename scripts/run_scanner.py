#!/usr/bin/env python3
"""
Standalone scanner for debugging and testing.
Scans markets without posting to Twitter.
"""

import asyncio
import sys
sys.path.insert(0, ".")

from dotenv import load_dotenv
load_dotenv()

from polymarket_client import PolymarketClient, build_proxy_url
from edge_detector import EdgeDetector


async def main():
    print("Cilia AI Market Scanner")
    print("=" * 50)

    # Initialize
    proxy_url = build_proxy_url()
    client = PolymarketClient(proxy_url=proxy_url)
    detector = EdgeDetector(
        min_odds_change=0.03,  # Lower threshold for testing
        min_volume_usd=500,
    )

    try:
        # Fetch markets
        print("\nFetching markets...")
        markets = await client.get_markets(limit=50)
        print(f"Found {len(markets)} markets")

        # Display top markets by volume
        print("\nTop markets by 24h volume:")
        print("-" * 50)

        markets_sorted = sorted(markets, key=lambda m: m.volume_24h, reverse=True)
        for i, m in enumerate(markets_sorted[:10], 1):
            print(f"{i}. {m.question[:60]}...")
            print(f"   YES: {m.yes_price*100:.0f}c | NO: {m.no_price*100:.0f}c | Vol: ${m.volume_24h:,.0f}")
            print()

        # Scan for edges
        print("\nScanning for edges...")
        print("-" * 50)

        edges = await detector.scan_all_markets(client, limit=50)

        if edges:
            print(f"\nFound {len(edges)} potential edges:\n")
            for edge in edges[:5]:
                print(f"Type: {edge.edge_type}")
                print(f"Market: {edge.market.question[:60]}...")
                print(f"Direction: {edge.direction}")
                print(f"Magnitude: {edge.magnitude:.1f}")
                print(f"Confidence: {edge.confidence}")
                print(f"Description: {edge.description}")
                print("-" * 30)
        else:
            print("No edges detected (need more price history)")

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
