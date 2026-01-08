"""
Market Scanner - continuous orderbook monitoring
"""

import asyncio
from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class MarketSnapshot:
    """Point-in-time snapshot of a market"""
    condition_id: str
    timestamp: datetime
    yes_price: float
    no_price: float
    yes_bid_depth: float
    yes_ask_depth: float
    spread: float
    volume_24h: float


@dataclass
class MarketHistory:
    """Rolling history for a market"""
    condition_id: str
    snapshots: list[MarketSnapshot] = field(default_factory=list)
    max_history: int = 100

    def add_snapshot(self, snapshot: MarketSnapshot):
        self.snapshots.append(snapshot)
        if len(self.snapshots) > self.max_history:
            self.snapshots = self.snapshots[-self.max_history:]

    def get_price_change(self, minutes: int = 60) -> Optional[float]:
        """Get price change over last N minutes"""
        if len(self.snapshots) < 2:
            return None

        cutoff = datetime.now() - timedelta(minutes=minutes)
        old_snapshots = [s for s in self.snapshots if s.timestamp < cutoff]

        if not old_snapshots:
            return None

        old_price = old_snapshots[0].yes_price
        current_price = self.snapshots[-1].yes_price
        return current_price - old_price

    def get_volume_trend(self) -> str:
        """Analyze volume trend"""
        if len(self.snapshots) < 5:
            return "unknown"

        recent = self.snapshots[-5:]
        volumes = [s.volume_24h for s in recent]

        if all(volumes[i] <= volumes[i+1] for i in range(len(volumes)-1)):
            return "increasing"
        elif all(volumes[i] >= volumes[i+1] for i in range(len(volumes)-1)):
            return "decreasing"
        return "stable"


class MarketScanner:
    """
    Continuous market scanner that maintains rolling history
    and detects market microstructure patterns
    """

    def __init__(self, polymarket_client):
        self.client = polymarket_client
        self.histories: dict[str, MarketHistory] = {}
        self.scan_count = 0

    async def scan(self, limit: int = 50) -> list[MarketSnapshot]:
        """Perform a single scan of top markets"""
        self.scan_count += 1
        snapshots = []

        markets = await self.client.get_markets(limit=limit)

        for market in markets:
            # Fetch orderbook for depth analysis
            orderbook = await self.client.get_orderbook(market.yes_token_id)

            bid_depth = 0
            ask_depth = 0
            spread = 0

            if orderbook:
                bid_depth = sum(b.size for b in orderbook.bids[:5])
                ask_depth = sum(a.size for a in orderbook.asks[:5])
                spread = orderbook.spread

            snapshot = MarketSnapshot(
                condition_id=market.condition_id,
                timestamp=datetime.now(),
                yes_price=market.yes_price,
                no_price=market.no_price,
                yes_bid_depth=bid_depth,
                yes_ask_depth=ask_depth,
                spread=spread,
                volume_24h=market.volume_24h,
            )

            snapshots.append(snapshot)

            # Update history
            if market.condition_id not in self.histories:
                self.histories[market.condition_id] = MarketHistory(
                    condition_id=market.condition_id
                )
            self.histories[market.condition_id].add_snapshot(snapshot)

        return snapshots

    def get_history(self, condition_id: str) -> Optional[MarketHistory]:
        """Get history for a specific market"""
        return self.histories.get(condition_id)

    def get_active_markets(self) -> int:
        """Get count of markets being tracked"""
        return len(self.histories)
