"""
Momentum Detection Strategy

Identifies significant price movements using exponential
weighted moving averages and velocity calculations.

Mathematical basis:
    velocity(t) = price(t) - price(t-1)
    momentum = EWMA(velocity, alpha)

    Signal triggered when |momentum| > threshold
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from collections import deque


@dataclass
class MomentumSignal:
    market_id: str
    current_price: float
    price_change: float
    momentum_score: float
    direction: str  # "bullish" or "bearish"
    confidence: str
    detected_at: datetime


class MomentumDetector:
    """
    Detects price momentum using EWMA of price velocity.

    Maintains rolling history of prices and calculates
    exponentially weighted momentum signals.
    """

    def __init__(
        self,
        ewma_alpha: float = 0.3,
        threshold: float = 0.05,
        min_history: int = 3,
    ):
        self.alpha = ewma_alpha
        self.threshold = threshold
        self.min_history = min_history
        self.price_history: dict[str, deque] = {}
        self.ewma_values: dict[str, float] = {}

    def update(
        self,
        market_id: str,
        price: float,
    ) -> Optional[MomentumSignal]:
        """
        Update price history and detect momentum signals.

        Args:
            market_id: Unique market identifier
            price: Current price (0-1)

        Returns:
            MomentumSignal if significant momentum detected
        """
        # Initialize history if needed
        if market_id not in self.price_history:
            self.price_history[market_id] = deque(maxlen=50)
            self.ewma_values[market_id] = 0

        history = self.price_history[market_id]
        history.append(price)

        # Need minimum history
        if len(history) < self.min_history:
            return None

        # Calculate velocity (price change)
        velocity = price - history[-2]

        # Update EWMA
        # EWMA(t) = alpha * velocity(t) + (1-alpha) * EWMA(t-1)
        old_ewma = self.ewma_values[market_id]
        new_ewma = self.alpha * velocity + (1 - self.alpha) * old_ewma
        self.ewma_values[market_id] = new_ewma

        # Check threshold
        if abs(new_ewma) > self.threshold:
            # Calculate total price change from start of history
            total_change = price - history[0]

            # Determine confidence based on magnitude
            magnitude = abs(new_ewma)
            if magnitude > self.threshold * 2:
                confidence = "high"
            elif magnitude > self.threshold * 1.5:
                confidence = "medium"
            else:
                confidence = "low"

            return MomentumSignal(
                market_id=market_id,
                current_price=price,
                price_change=total_change,
                momentum_score=new_ewma,
                direction="bullish" if new_ewma > 0 else "bearish",
                confidence=confidence,
                detected_at=datetime.now(),
            )

        return None

    def get_momentum(self, market_id: str) -> float:
        """Get current momentum value for a market"""
        return self.ewma_values.get(market_id, 0)

    def reset_market(self, market_id: str):
        """Reset history for a market"""
        if market_id in self.price_history:
            del self.price_history[market_id]
        if market_id in self.ewma_values:
            del self.ewma_values[market_id]
