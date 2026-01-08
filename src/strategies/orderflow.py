"""
Order Flow Analysis Strategy

Analyzes orderbook imbalances to detect informed trading
and institutional activity.

Mathematical basis:
    imbalance_ratio = sum(bid_volume[:N]) / sum(ask_volume[:N])

    Buy pressure when: ratio > 3.0 (heavy bids)
    Sell pressure when: ratio < 0.33 (heavy asks)

This strategy uses VPIN-inspired concepts to identify
toxic (informed) order flow.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from collections import deque


@dataclass
class OrderFlowSignal:
    market_id: str
    bid_volume: float
    ask_volume: float
    imbalance_ratio: float
    direction: str  # "buy_pressure" or "sell_pressure"
    toxicity_score: float  # 0-1, higher = more informed flow
    detected_at: datetime


class OrderFlowAnalyzer:
    """
    Analyzes orderbook flow for signs of informed trading.

    Tracks bid/ask imbalances and volume patterns to identify
    markets where smart money may be positioning.
    """

    def __init__(
        self,
        buy_threshold: float = 3.0,
        sell_threshold: float = 0.33,
        depth_levels: int = 5,
        volume_bucket_size: float = 1000,
    ):
        self.buy_threshold = buy_threshold
        self.sell_threshold = sell_threshold
        self.depth_levels = depth_levels
        self.volume_bucket_size = volume_bucket_size

        # Track volume history for VPIN calculation
        self.buy_volume_history: dict[str, deque] = {}
        self.sell_volume_history: dict[str, deque] = {}

    def analyze(
        self,
        market_id: str,
        bids: list[tuple[float, float]],  # [(price, size), ...]
        asks: list[tuple[float, float]],
    ) -> Optional[OrderFlowSignal]:
        """
        Analyze orderbook for flow imbalances.

        Args:
            market_id: Unique market identifier
            bids: List of (price, size) tuples for bids
            asks: List of (price, size) tuples for asks

        Returns:
            OrderFlowSignal if significant imbalance detected
        """
        if not bids or not asks:
            return None

        # Sum volume at top N levels
        bid_volume = sum(size for _, size in bids[:self.depth_levels])
        ask_volume = sum(size for _, size in asks[:self.depth_levels])

        if ask_volume == 0:
            return None

        ratio = bid_volume / ask_volume

        # Check for significant imbalance
        signal = None

        if ratio > self.buy_threshold:
            signal = OrderFlowSignal(
                market_id=market_id,
                bid_volume=bid_volume,
                ask_volume=ask_volume,
                imbalance_ratio=ratio,
                direction="buy_pressure",
                toxicity_score=self._calculate_toxicity(market_id, ratio, "buy"),
                detected_at=datetime.now(),
            )

        elif ratio < self.sell_threshold:
            signal = OrderFlowSignal(
                market_id=market_id,
                bid_volume=bid_volume,
                ask_volume=ask_volume,
                imbalance_ratio=ratio,
                direction="sell_pressure",
                toxicity_score=self._calculate_toxicity(market_id, ratio, "sell"),
                detected_at=datetime.now(),
            )

        # Update volume history for VPIN
        self._update_volume_history(market_id, bid_volume, ask_volume)

        return signal

    def _calculate_toxicity(
        self,
        market_id: str,
        ratio: float,
        direction: str,
    ) -> float:
        """
        Calculate toxicity score (proxy for informed trading).

        Uses simplified VPIN concept:
        VPIN = |V_buy - V_sell| / (V_buy + V_sell)
        """
        if market_id not in self.buy_volume_history:
            # Not enough history, use ratio-based estimate
            if direction == "buy":
                return min((ratio - 1) / 5, 1.0)
            else:
                return min((1/ratio - 1) / 5, 1.0)

        buy_hist = list(self.buy_volume_history[market_id])
        sell_hist = list(self.sell_volume_history[market_id])

        if not buy_hist or not sell_hist:
            return 0.5

        total_buy = sum(buy_hist)
        total_sell = sum(sell_hist)
        total = total_buy + total_sell

        if total == 0:
            return 0.5

        vpin = abs(total_buy - total_sell) / total
        return min(vpin, 1.0)

    def _update_volume_history(
        self,
        market_id: str,
        bid_volume: float,
        ask_volume: float,
    ):
        """Update rolling volume history"""
        if market_id not in self.buy_volume_history:
            self.buy_volume_history[market_id] = deque(maxlen=20)
            self.sell_volume_history[market_id] = deque(maxlen=20)

        self.buy_volume_history[market_id].append(bid_volume)
        self.sell_volume_history[market_id].append(ask_volume)

    def get_vpin(self, market_id: str) -> Optional[float]:
        """Get current VPIN estimate for a market"""
        if market_id not in self.buy_volume_history:
            return None

        buy_hist = list(self.buy_volume_history[market_id])
        sell_hist = list(self.sell_volume_history[market_id])

        total_buy = sum(buy_hist)
        total_sell = sum(sell_hist)
        total = total_buy + total_sell

        if total == 0:
            return None

        return abs(total_buy - total_sell) / total
