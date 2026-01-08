"""
Risk Calculator - computes composite risk scores
"""

import math
from datetime import datetime
from typing import Optional
from dataclasses import dataclass


@dataclass
class RiskMetrics:
    """Detailed risk breakdown"""
    liquidity_risk: float  # 0-1, higher = riskier
    time_risk: float       # 0-1, closer to expiry = riskier
    volatility_risk: float # 0-1, higher vol = riskier
    spread_risk: float     # 0-1, wider spread = riskier
    composite_score: float # weighted average
    risk_tier: str         # "low", "medium", "high"


class RiskCalculator:
    """
    Calculates multi-factor risk scores for prediction market signals.

    Risk Model:
    - Liquidity risk: Based on orderbook depth relative to position size
    - Time decay risk: Exponential decay as resolution approaches
    - Volatility risk: Based on recent price variance
    - Spread risk: Bid-ask spread as % of mid price

    Composite = w1*liquidity + w2*time + w3*volatility + w4*spread
    """

    def __init__(
        self,
        liquidity_weight: float = 0.30,
        time_weight: float = 0.25,
        volatility_weight: float = 0.25,
        spread_weight: float = 0.20,
    ):
        self.weights = {
            "liquidity": liquidity_weight,
            "time": time_weight,
            "volatility": volatility_weight,
            "spread": spread_weight,
        }

        # Thresholds for risk tiers
        self.low_threshold = 0.33
        self.high_threshold = 0.66

    def calculate_liquidity_risk(
        self,
        bid_depth: float,
        ask_depth: float,
        min_depth: float = 1000,
    ) -> float:
        """
        Liquidity risk based on orderbook depth.
        Lower depth = higher risk.
        """
        total_depth = bid_depth + ask_depth

        if total_depth >= min_depth * 10:
            return 0.1  # Very liquid
        elif total_depth >= min_depth * 5:
            return 0.3
        elif total_depth >= min_depth:
            return 0.5
        elif total_depth >= min_depth * 0.5:
            return 0.7
        else:
            return 0.9  # Very illiquid

    def calculate_time_risk(
        self,
        end_date: Optional[str],
        decay_lambda: float = 0.1,
    ) -> float:
        """
        Time decay risk using exponential model.
        Closer to expiry = higher risk (less time for thesis to play out).
        """
        if not end_date:
            return 0.5  # Unknown expiry = medium risk

        try:
            expiry = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            days_to_expiry = (expiry - datetime.now(expiry.tzinfo)).days

            if days_to_expiry <= 0:
                return 1.0  # Expired or expiring today
            elif days_to_expiry > 365:
                return 0.1  # Very long dated

            # Exponential decay: risk = 1 - e^(-lambda * days)
            # Inverted so shorter time = higher risk
            risk = 1 - math.exp(-decay_lambda * (365 - days_to_expiry) / 365)
            return min(max(risk, 0), 1)

        except (ValueError, TypeError):
            return 0.5

    def calculate_volatility_risk(
        self,
        price_history: list[float],
        window: int = 10,
    ) -> float:
        """
        Volatility risk based on recent price variance.
        Higher variance = higher risk.
        """
        if len(price_history) < 2:
            return 0.5

        recent = price_history[-window:]

        # Calculate standard deviation
        mean = sum(recent) / len(recent)
        variance = sum((x - mean) ** 2 for x in recent) / len(recent)
        std = math.sqrt(variance)

        # Normalize: std of 0.05 (5%) is medium risk
        # std of 0.10 (10%) is high risk
        risk = min(std / 0.10, 1.0)
        return risk

    def calculate_spread_risk(
        self,
        spread: float,
        mid_price: float,
    ) -> float:
        """
        Spread risk as percentage of mid price.
        Wider spread = higher risk (harder to exit).
        """
        if mid_price <= 0:
            return 0.5

        spread_pct = spread / mid_price

        # 1% spread = low risk, 5% = medium, 10%+ = high
        if spread_pct < 0.01:
            return 0.1
        elif spread_pct < 0.03:
            return 0.3
        elif spread_pct < 0.05:
            return 0.5
        elif spread_pct < 0.10:
            return 0.7
        else:
            return 0.9

    def calculate(
        self,
        bid_depth: float,
        ask_depth: float,
        end_date: Optional[str],
        price_history: list[float],
        spread: float,
        mid_price: float,
    ) -> RiskMetrics:
        """Calculate complete risk metrics"""
        liquidity = self.calculate_liquidity_risk(bid_depth, ask_depth)
        time = self.calculate_time_risk(end_date)
        volatility = self.calculate_volatility_risk(price_history)
        spread_risk = self.calculate_spread_risk(spread, mid_price)

        # Weighted composite
        composite = (
            self.weights["liquidity"] * liquidity +
            self.weights["time"] * time +
            self.weights["volatility"] * volatility +
            self.weights["spread"] * spread_risk
        )

        # Determine tier
        if composite < self.low_threshold:
            tier = "low"
        elif composite < self.high_threshold:
            tier = "medium"
        else:
            tier = "high"

        return RiskMetrics(
            liquidity_risk=liquidity,
            time_risk=time,
            volatility_risk=volatility,
            spread_risk=spread_risk,
            composite_score=composite,
            risk_tier=tier,
        )
