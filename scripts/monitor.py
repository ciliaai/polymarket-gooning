#!/usr/bin/env python3
"""
Real-time market monitor - shows hot markets and detected signals
Run this to see what the bot would post
"""

import asyncio
import sys
sys.path.insert(0, ".")

from dotenv import load_dotenv
load_dotenv()

from polymarket_client import PolymarketClient, build_proxy_url
from edge_detector import EdgeDetector


async def monitor():
    print("=" * 60)
    print("Cilia AI Market Monitor")
    print("=" * 60)

    client = PolymarketClient(proxy_url=build_proxy_url())
    detector = EdgeDetector(
        min_odds_change=0.03,  # 3% threshold for testing
        min_volume_usd=500,
    )

    scan_count = 0

    try:
        while True:
            scan_count += 1
            print(f"\n[Scan #{scan_count}] Fetching markets...")

            markets = await client.get_markets(limit=50)
            print(f"Found {len(markets)} active markets")

            if not markets:
                print("No markets returned - API may be rate limiting")
                await asyncio.sleep(60)
                continue

            # Show top 5 by volume
            print("\n--- HOT MARKETS (by 24h volume) ---")
            by_volume = sorted(markets, key=lambda m: m.volume_24h, reverse=True)[:5]
            for i, m in enumerate(by_volume, 1):
                print(f"{i}. {m.question[:55]}...")
                print(f"   YES: {m.yes_price*100:.0f}c | NO: {m.no_price*100:.0f}c | Vol: ${m.volume_24h:,.0f}")

            # Run edge detection
            print("\n--- SCANNING FOR SIGNALS ---")
            edges = await detector.scan_all_markets(client, limit=50)

            if edges:
                print(f"\nDETECTED {len(edges)} SIGNALS:\n")
                for edge in edges[:5]:
                    print(f"[{edge.edge_type.upper()}] {edge.market.question[:50]}...")
                    print(f"  Direction: {edge.direction}")
                    print(f"  Confidence: {edge.confidence}")
                    print(f"  Magnitude: {edge.magnitude:.1f}")
                    print(f"  {edge.description}")
                    print()
            else:
                print("No signals detected (building price history...)")
                print(f"Tracking {len(detector.price_history)} markets")

            print("\n" + "-" * 60)
            print("Next scan in 30 seconds...")
            await asyncio.sleep(30)

    except KeyboardInterrupt:
        print("\nStopping monitor...")
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(monitor())
