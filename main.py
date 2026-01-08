#!/usr/bin/env python3
"""
Cilia AI - Polymarket Edge Detection Bot
Monitors prediction markets and posts signals to X as they're detected

Usage:
    python main.py              # Run the bot
    python main.py --dry-run    # Test without posting to Twitter
    python main.py --once       # Run once and exit (for testing)
"""

import asyncio
import argparse
import os
import tempfile
from datetime import datetime, timedelta
from dotenv import load_dotenv

from polymarket_client import PolymarketClient, build_proxy_url
from edge_detector import EdgeDetector, Edge
from image_generator import GrokImageGenerator
from twitter_client import TwitterClient, DryRunTwitterClient


load_dotenv()

DAILY_POST_LIMIT = 15  # Free tier is 17, we stay safe at 15


def compute_risk_level(edge: Edge) -> str:
    """Compute risk level for an edge signal based on alpha score"""
    # Arbitrage = free money = low risk
    if edge.edge_type == "arbitrage":
        return "low"

    # High alpha score = better signal = lower risk
    if edge.alpha_score > 70:
        return "low"
    if edge.alpha_score > 40:
        return "medium"

    # Whale activity with high confidence = low risk
    if edge.edge_type == "whale_activity" and edge.confidence == "high":
        return "low"

    # High confidence + high magnitude = lower risk
    if edge.confidence == "high" and edge.magnitude > 15:
        return "low"

    # Orderbook imbalance without whale confirmation = higher risk
    if edge.edge_type == "orderbook_imbalance":
        return "medium" if edge.confidence == "high" else "high"

    if edge.confidence == "medium" and edge.magnitude > 10:
        return "medium"

    return "medium" if edge.confidence != "low" else "high"


def format_signal_tweet(edge: Edge) -> str:
    """Format a single signal as a tweet (legacy)"""
    risk = compute_risk_level(edge)
    question = edge.market.question
    if len(question) > 120:
        question = question[:117] + "..."

    lines = [
        f"senal detectada~ (nicolas could never)",
        "",
        question,
        "",
    ]

    if edge.direction in ["YES", "NO"]:
        price = edge.market.yes_price if edge.direction == "YES" else edge.market.no_price
        lines.append(f"{edge.direction} @ {price*100:.0f}c")

    lines.extend([
        f"type: {edge.edge_type.replace('_', ' ')}",
        f"risk: {risk}",
        "",
        edge.description,
        "",
        f"polymarket.com/event/{edge.market.slug}",
    ])

    return "\n".join(lines)


def format_grouped_tweet(edges: list[Edge]) -> str:
    """Format 3 signals into one grouped tweet"""
    if not edges:
        return None

    lines = ["senal detectada~ my husband printed money, i print alpha~", ""]

    for i, edge in enumerate(edges[:3], 1):
        question = edge.market.question
        if len(question) > 55:
            question = question[:52] + "..."

        risk = compute_risk_level(edge)

        # Format signal type shorthand
        sig_type = edge.edge_type.replace("_", " ")
        if edge.edge_type == "volume_spike":
            # Extract z-score or multiplier from description
            if "z=" in edge.description:
                z_part = edge.description.split("z=")[1].split(",")[0]
                sig_info = f"vol z={z_part}"
            elif "x normal" in edge.description or "x avg" in edge.description:
                mult = edge.description.split("(")[1].split("x")[0] if "(" in edge.description else ""
                if mult:
                    sig_info = f"vol {mult}x"
            else:
                sig_info = "volume spike"
        elif edge.edge_type == "odds_movement":
            if "strong momentum" in edge.description:
                sig_info = "strong momentum"
            elif "accelerating" in edge.description:
                sig_info = "accelerating"
            else:
                sig_info = "odds moving"
        elif edge.edge_type == "orderbook_imbalance":
            sig_info = "orderbook imbalance"
        elif edge.edge_type == "whale_activity":
            sig_info = "whale alert"
        elif edge.edge_type == "arbitrage":
            sig_info = "arb opportunity"
        else:
            sig_info = sig_type

        # Price display
        if edge.direction == "YES":
            price_str = f"YES @ {edge.market.yes_price*100:.0f}c"
        elif edge.direction == "NO":
            price_str = f"NO @ {edge.market.no_price*100:.0f}c"
        else:
            price_str = f"YES @ {edge.market.yes_price*100:.0f}c"

        lines.append(f"{i}. {question}")
        lines.append(f"   {price_str} | {sig_info}")
        lines.append(f"   polymarket.com/event/{edge.market.slug}")
        lines.append("")

    return "\n".join(lines)


class CiliaBot:
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run

        proxy_url = build_proxy_url()
        self.polymarket = PolymarketClient(proxy_url=proxy_url)
        self.detector = EdgeDetector(
            min_odds_change=float(os.getenv("MIN_ODDS_CHANGE_PERCENT", "5")) / 100,
            min_volume_usd=float(os.getenv("MIN_VOLUME_USD", "1000")),
        )
        self.image_gen = GrokImageGenerator()

        if dry_run:
            self.twitter = DryRunTwitterClient()
        else:
            self.twitter = TwitterClient()

        self.posts_today = 0
        self.last_reset_date = datetime.now().date()
        self.posted_markets: dict[str, datetime] = {}
        self.market_cooldown_hours = 4

        # Track posted signal combinations to avoid duplicates
        self.posted_combos: set[tuple] = set()

    def _reset_daily_counter(self):
        """Reset post counter if new day"""
        today = datetime.now().date()
        if today != self.last_reset_date:
            self.posts_today = 0
            self.last_reset_date = today
            print(f"New day - reset post counter")

    def _can_post(self) -> bool:
        """Check if we can post (under daily limit)"""
        self._reset_daily_counter()
        return self.posts_today < DAILY_POST_LIMIT

    def _should_post_signal(self, edge: Edge) -> bool:
        """Check if this signal should be posted"""
        if not self._can_post():
            return False

        # Check market cooldown
        key = edge.market.condition_id
        if key in self.posted_markets:
            if datetime.now() - self.posted_markets[key] < timedelta(hours=self.market_cooldown_hours):
                return False

        # Only post medium+ confidence
        if edge.confidence == "low":
            return False

        # Minimum magnitude
        if edge.magnitude < 8:
            return False

        return True

    def _get_combo_signature(self, edges: list[Edge]) -> tuple:
        """Create a unique signature for a combination of signals"""
        # Sort by condition_id to ensure consistent ordering
        sig_parts = sorted([
            (e.market.condition_id, e.edge_type)
            for e in edges
        ])
        return tuple(sig_parts)

    def _is_duplicate_combo(self, edges: list[Edge]) -> bool:
        """Check if this exact signal combo was already posted"""
        sig = self._get_combo_signature(edges)
        return sig in self.posted_combos

    def _mark_combo_posted(self, edges: list[Edge]):
        """Mark this signal combo as posted"""
        sig = self._get_combo_signature(edges)
        self.posted_combos.add(sig)

    async def post_grouped_signals(self, edges: list[Edge]) -> bool:
        """Post 3 grouped signals to Twitter with one image"""
        if len(edges) < 1:
            return False

        # Take top 3 by magnitude
        top_edges = sorted(edges, key=lambda e: e.magnitude, reverse=True)[:3]

        # Check if this exact combo was already posted
        if self._is_duplicate_combo(top_edges):
            print(f"\nSkipping duplicate combo - these 3 signals were already posted")
            return False

        tweet_text = format_grouped_tweet(top_edges)

        print(f"\nPosting {len(top_edges)} grouped signals...")
        for e in top_edges:
            print(f"  - {e.edge_type}: {e.market.question[:40]}...")

        # Try to generate image based on top signal
        image_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
                image_path = tmp.name

            image_success = await self.image_gen.generate_and_save(top_edges[0], image_path)
            if not image_success:
                print("Image generation failed, posting without image")
                image_path = None

        except Exception as e:
            print(f"Image error: {e}")
            image_path = None

        # Post tweet
        try:
            tweet_url = self.twitter.post_tweet(tweet_text, media_path=image_path)

            if tweet_url:
                print(f"Posted: {tweet_url}")
                self.posts_today += 1
                # Mark all markets as posted
                for edge in top_edges:
                    self.posted_markets[edge.market.condition_id] = datetime.now()
                # Mark this combo as posted to avoid duplicates
                self._mark_combo_posted(top_edges)
                return True
            else:
                print("Post failed")
                return False

        except Exception as e:
            print(f"Twitter error: {e}")
            return False

        finally:
            if image_path:
                try:
                    os.unlink(image_path)
                except:
                    pass

    async def run_scan(self) -> list[Edge]:
        """Run a single scan cycle"""
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Scanning markets...")

        try:
            edges = await self.detector.scan_all_markets(self.polymarket, limit=50)
            print(f"Found {len(edges)} potential edges")

            # Filter to postable signals
            postable = [e for e in edges if self._should_post_signal(e)]
            print(f"Postable: {len(postable)} signals")

            return postable

        except Exception as e:
            print(f"Scan error: {e}")
            import traceback
            traceback.print_exc()
            return []

    async def run_once(self):
        """Run a single scan and post cycle"""
        edges = await self.run_scan()

        if edges and len(edges) >= 3 and self._can_post():
            await self.post_grouped_signals(edges[:3])

        await self.polymarket.close()

    async def run_loop(self):
        """Run continuous monitoring loop"""
        scan_interval = int(os.getenv("CHECK_INTERVAL_SECONDS", "180"))

        print(f"\nCilia AI Bot Started!")
        print(f"Scanning every {scan_interval} seconds")
        print(f"Daily limit: {DAILY_POST_LIMIT} posts")
        print(f"Dry run: {self.dry_run}")
        print("-" * 50)

        try:
            while True:
                self._reset_daily_counter()

                if not self._can_post():
                    print(f"Daily limit reached ({self.posts_today}/{DAILY_POST_LIMIT}). Waiting for tomorrow...")
                    await asyncio.sleep(3600)  # Check again in an hour
                    continue

                edges = await self.run_scan()

                # Post grouped signals (3 per tweet) if we have enough
                if edges and len(edges) >= 3 and self._can_post():
                    await self.post_grouped_signals(edges[:3])

                # Clean up old cooldowns
                cutoff = datetime.now() - timedelta(hours=8)
                self.posted_markets = {k: v for k, v in self.posted_markets.items() if v > cutoff}

                print(f"Posts today: {self.posts_today}/{DAILY_POST_LIMIT}")
                print(f"Next scan in {scan_interval} seconds...")
                await asyncio.sleep(scan_interval)

        except KeyboardInterrupt:
            print("\nShutting down...")
        finally:
            await self.polymarket.close()


async def main():
    parser = argparse.ArgumentParser(description="Cilia AI Polymarket Bot")
    parser.add_argument("--dry-run", action="store_true", help="Test without posting")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    args = parser.parse_args()

    bot = CiliaBot(dry_run=args.dry_run)

    if args.once:
        await bot.run_once()
    else:
        await bot.run_loop()


if __name__ == "__main__":
    asyncio.run(main())
