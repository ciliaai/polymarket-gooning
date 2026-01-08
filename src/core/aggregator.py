"""
Signal Aggregator - combines multiple signals for hourly digests
"""

from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class AggregatedSignal:
    """A signal ready for posting"""
    market_id: str
    market_question: str
    market_slug: str
    direction: str
    price: float
    signal_types: list[str]
    confidence: str
    risk_level: str
    magnitude: float
    detected_at: datetime


class SignalAggregator:
    """
    Aggregates signals over time and prepares hourly digests.
    Implements deduplication and priority ranking.
    """

    def __init__(self, digest_interval_hours: float = 1.0):
        self.digest_interval = timedelta(hours=digest_interval_hours)
        self.pending_signals: dict[str, list] = defaultdict(list)
        self.last_digest_time = datetime.now()
        self.posted_markets: dict[str, datetime] = {}
        self.market_cooldown = timedelta(hours=4)

    def add_signal(self, signal: AggregatedSignal):
        """Add a signal to pending queue"""
        # Check cooldown
        if signal.market_id in self.posted_markets:
            if datetime.now() - self.posted_markets[signal.market_id] < self.market_cooldown:
                return False

        # Add to pending, grouped by market
        self.pending_signals[signal.market_id].append(signal)
        return True

    def should_post_digest(self) -> bool:
        """Check if it's time for next digest"""
        time_since_last = datetime.now() - self.last_digest_time
        has_signals = len(self.pending_signals) > 0
        return time_since_last >= self.digest_interval and has_signals

    def get_digest(self, max_signals: int = 5) -> list[AggregatedSignal]:
        """
        Get top signals for digest.
        Combines multiple signal types per market.
        """
        if not self.pending_signals:
            return []

        # For each market, merge signals
        merged = []
        for market_id, signals in self.pending_signals.items():
            if not signals:
                continue

            # Use most recent signal as base
            best = max(signals, key=lambda s: s.magnitude)

            # Combine signal types
            all_types = list(set(s.signal_types[0] for s in signals if s.signal_types))
            best.signal_types = all_types

            merged.append(best)

        # Sort by magnitude
        merged.sort(key=lambda s: s.magnitude, reverse=True)

        return merged[:max_signals]

    def mark_posted(self, signals: list[AggregatedSignal]):
        """Mark signals as posted and clear from pending"""
        for signal in signals:
            self.posted_markets[signal.market_id] = datetime.now()
            if signal.market_id in self.pending_signals:
                del self.pending_signals[signal.market_id]

        self.last_digest_time = datetime.now()

    def get_stats(self) -> dict:
        """Get aggregator statistics"""
        return {
            "pending_markets": len(self.pending_signals),
            "total_pending_signals": sum(len(s) for s in self.pending_signals.values()),
            "posted_markets_in_cooldown": len(self.posted_markets),
            "time_until_digest": str(self.digest_interval - (datetime.now() - self.last_digest_time)),
        }
