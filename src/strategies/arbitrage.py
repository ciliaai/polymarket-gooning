"""
Arbitrage Detection Strategy

Identifies risk-free profit opportunities when market makers
misprice binary outcomes such that P(YES) + P(NO) < 1.00

Mathematical basis:
    In efficient binary markets: P(YES) + P(NO) = 1.00
    Arbitrage exists when: P(YES) + P(NO) < 1.00
    Profit = 1 - (P_yes + P_no) per $1 deployed

This strategy monitors for pricing dislocations and
calculates the theoretical profit margin.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class ArbitrageSignal:
    market_id: str
    yes_price: float
    no_price: float
    gap: float  # theoretical profit in cents
    detected_at: datetime


class ArbitrageDetector:
    """
    Detects arbitrage opportunities in binary prediction markets.

    The detector continuously monitors the sum of YES + NO prices.
    When this sum falls below the threshold, an arbitrage exists.
    """

    def __init__(
        self,
        threshold: float = 0.98,  # 2 cent minimum gap
        min_gap_cents: float = 1.0,
    ):
        self.threshold = threshold
        self.min_gap_cents = min_gap_cents
        self.signals_detected = 0

    def detect(
        self,
        market_id: str,
        yes_price: float,
        no_price: float,
    ) -> Optional[ArbitrageSignal]:
        """
        Check if arbitrage exists in this market.

        Args:
            market_id: Unique market identifier
            yes_price: Current YES price (0-1)
            no_price: Current NO price (0-1)

        Returns:
            ArbitrageSignal if opportunity exists, None otherwise
        """
        total = yes_price + no_price

        if total < self.threshold:
            gap = (1 - total) * 100  # Convert to cents

            if gap >= self.min_gap_cents:
                self.signals_detected += 1

                return ArbitrageSignal(
                    market_id=market_id,
                    yes_price=yes_price,
                    no_price=no_price,
                    gap=gap,
                    detected_at=datetime.now(),
                )

        return None

    def calculate_position_size(
        self,
        gap: float,
        max_position: float = 1000,
        kelly_fraction: float = 0.25,
    ) -> float:
        """
        Calculate optimal position size using Kelly criterion.

        For pure arbitrage (risk-free), Kelly suggests going all-in,
        but we apply a fractional Kelly for safety.

        Args:
            gap: Arbitrage gap in cents
            max_position: Maximum position in USD
            kelly_fraction: Fraction of Kelly to use (0.25 = quarter Kelly)

        Returns:
            Recommended position size in USD
        """
        # For arbitrage, edge = gap (in decimal)
        edge = gap / 100

        # Kelly: f* = edge / variance, but for arbitrage variance -> 0
        # So we cap at kelly_fraction * max_position
        return min(max_position * kelly_fraction * (edge / 0.02), max_position)
