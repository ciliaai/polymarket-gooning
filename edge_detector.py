"""
Edge Detection Engine
Identifies trading opportunities from Polymarket data

Strategies:
- Arbitrage: YES + NO < 98c = free money
- Momentum: EWMA-based price velocity detection
- Volume Anomaly: Z-score based spike detection
- Orderbook Imbalance: Bid/ask ratio + whale detection
- Smart Money: Large order clustering analysis
"""

import os
import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional
from polymarket_client import Market, OrderBook, PolymarketClient


@dataclass
class Edge:
    market: Market
    edge_type: str  # "arbitrage", "odds_movement", "volume_spike", "orderbook_imbalance", "whale_activity"
    description: str
    confidence: str  # "low", "medium", "high"
    magnitude: float  # how significant is the edge (0-100)
    direction: str  # "YES", "NO", or "NEUTRAL"
    detected_at: datetime
    alpha_score: float = 0.0  # combined quality score

    def to_tweet_text(self) -> str:
        """Generate tweet text for this edge"""
        emoji_map = {
            "arbitrage": "free money alert",
            "odds_movement": "big move detected",
            "volume_spike": "money flowing in",
            "orderbook_imbalance": "smart money signal",
        }

        direction_emoji = "^" if self.direction == "YES" else "v" if self.direction == "NO" else "~"

        lines = [
            f"{emoji_map.get(self.edge_type, 'edge detected')}",
            f"",
            f"{self.market.question[:180]}",
            f"",
            f"{direction_emoji} {self.direction} @ {self.market.yes_price * 100:.0f}c" if self.direction == "YES"
                else f"{direction_emoji} {self.direction} @ {self.market.no_price * 100:.0f}c" if self.direction == "NO"
                else f"current: YES {self.market.yes_price * 100:.0f}c / NO {self.market.no_price * 100:.0f}c",
            f"",
            f"{self.description}",
            f"",
            f"polymarket.com/event/{self.market.slug}",
        ]
        return "\n".join(lines)


class EdgeDetector:
    def __init__(
        self,
        min_odds_change: float = 0.05,  # 5% minimum odds change
        min_volume_usd: float = 1000,   # minimum 24h volume
        arbitrage_threshold: float = 0.98,  # YES + NO < 98 cents = arb
        ewma_alpha: float = 0.3,  # EWMA smoothing factor (higher = more reactive)
    ):
        self.min_odds_change = min_odds_change
        self.min_volume_usd = min_volume_usd
        self.arbitrage_threshold = arbitrage_threshold
        self.ewma_alpha = ewma_alpha

        # Price tracking with EWMA
        self.price_history: dict[str, list[tuple[datetime, float, float]]] = {}
        self.ewma_prices: dict[str, tuple[float, float]] = {}  # smoothed YES/NO prices
        self.volume_history: dict[str, list[float]] = {}  # for z-score calculation

        # Whale detection thresholds
        self.whale_order_size = 5000  # $5k+ order = whale
        self.whale_cluster_threshold = 3  # 3+ whale orders = smart money

    def update_price(self, market: Market):
        """Track price over time with EWMA smoothing"""
        key = market.condition_id
        now = datetime.now()

        if key not in self.price_history:
            self.price_history[key] = []

        self.price_history[key].append((now, market.yes_price, market.no_price))

        # Keep only last 100 data points per market
        if len(self.price_history[key]) > 100:
            self.price_history[key] = self.price_history[key][-100:]

        # Update EWMA prices (exponential weighted moving average)
        if key not in self.ewma_prices:
            self.ewma_prices[key] = (market.yes_price, market.no_price)
        else:
            old_yes, old_no = self.ewma_prices[key]
            new_yes = self.ewma_alpha * market.yes_price + (1 - self.ewma_alpha) * old_yes
            new_no = self.ewma_alpha * market.no_price + (1 - self.ewma_alpha) * old_no
            self.ewma_prices[key] = (new_yes, new_no)

        # Track volume history for z-score
        if key not in self.volume_history:
            self.volume_history[key] = []
        self.volume_history[key].append(market.volume_24h)
        if len(self.volume_history[key]) > 20:
            self.volume_history[key] = self.volume_history[key][-20:]

    def detect_arbitrage(self, market: Market) -> Optional[Edge]:
        """Check if YES + NO prices sum to less than $1"""
        total = market.yes_price + market.no_price

        if total < self.arbitrage_threshold:
            gap = (1 - total) * 100
            return Edge(
                market=market,
                edge_type="arbitrage",
                description=f"market mispriced - {gap:.1f}c gap detected! YES + NO = {total*100:.0f}c",
                confidence="high",
                magnitude=gap,
                direction="NEUTRAL",
                detected_at=datetime.now(),
            )
        return None

    def detect_odds_movement(self, market: Market) -> Optional[Edge]:
        """Detect significant price movement using EWMA momentum"""
        key = market.condition_id
        history = self.price_history.get(key, [])

        if len(history) < 3:
            return None

        # Get EWMA smoothed price vs current - detects deviation from trend
        ewma_yes, ewma_no = self.ewma_prices.get(key, (market.yes_price, market.no_price))

        # Price velocity: current vs smoothed average
        deviation = market.yes_price - ewma_yes

        # Also check raw movement from oldest
        oldest_time, oldest_yes, oldest_no = history[0]
        raw_change = market.yes_price - oldest_yes

        # Calculate momentum score (combines velocity + acceleration)
        if len(history) >= 5:
            recent_prices = [h[1] for h in history[-5:]]
            velocity = recent_prices[-1] - recent_prices[0]
            acceleration = (recent_prices[-1] - recent_prices[-2]) - (recent_prices[1] - recent_prices[0])
            momentum_score = abs(velocity) * 100 + abs(acceleration) * 50
        else:
            momentum_score = abs(raw_change) * 100

        # Check if movement exceeds threshold
        if abs(raw_change) >= self.min_odds_change or abs(deviation) >= self.min_odds_change * 0.7:
            direction = "YES" if raw_change > 0 else "NO"
            change_pct = abs(raw_change) * 100

            # Determine trend strength
            if abs(deviation) > 0.03 and raw_change * deviation > 0:
                trend_desc = "strong momentum"
                confidence = "high"
            elif momentum_score > 15:
                trend_desc = "accelerating"
                confidence = "high"
            else:
                trend_desc = "moving"
                confidence = "medium"

            alpha = min(momentum_score + (market.liquidity / 10000), 100)

            return Edge(
                market=market,
                edge_type="odds_movement",
                description=f"{trend_desc} - YES {'+' if raw_change > 0 else ''}{raw_change*100:.1f}c | velocity: {deviation*100:+.1f}c",
                confidence=confidence,
                magnitude=change_pct + momentum_score * 0.5,
                direction=direction,
                detected_at=datetime.now(),
                alpha_score=alpha,
            )
        return None

    def detect_volume_spike(self, market: Market) -> Optional[Edge]:
        """Detect unusual volume using z-score anomaly detection"""
        key = market.condition_id
        vol_history = self.volume_history.get(key, [])

        # Use market's own liquidity as baseline, or global average
        baseline = max(market.liquidity * 0.1, 5000)  # 10% of liquidity or $5k

        # Calculate z-score if we have history
        if len(vol_history) >= 5:
            mean_vol = sum(vol_history) / len(vol_history)
            variance = sum((v - mean_vol) ** 2 for v in vol_history) / len(vol_history)
            std_vol = math.sqrt(variance) if variance > 0 else mean_vol * 0.5

            if std_vol > 0:
                z_score = (market.volume_24h - mean_vol) / std_vol
            else:
                z_score = 0

            # Z-score > 2 = unusual (95th percentile)
            if z_score > 2.0:
                spike_factor = market.volume_24h / mean_vol if mean_vol > 0 else 1

                # Higher z-score = higher confidence
                if z_score > 3.5:
                    confidence = "high"
                    desc = "massive volume anomaly"
                elif z_score > 2.5:
                    confidence = "high"
                    desc = "significant volume spike"
                else:
                    confidence = "medium"
                    desc = "volume spike"

                alpha = min(z_score * 20 + (market.liquidity / 5000), 100)

                return Edge(
                    market=market,
                    edge_type="volume_spike",
                    description=f"{desc}! ${market.volume_24h:,.0f} (z={z_score:.1f}, {spike_factor:.1f}x avg)",
                    confidence=confidence,
                    magnitude=min(z_score * 25, 100),
                    direction="NEUTRAL",
                    detected_at=datetime.now(),
                    alpha_score=alpha,
                )

        # Fallback: simple multiplier check for new markets
        elif market.volume_24h > baseline * 3:
            spike_factor = market.volume_24h / baseline

            return Edge(
                market=market,
                edge_type="volume_spike",
                description=f"volume spike! ${market.volume_24h:,.0f} in 24h ({spike_factor:.1f}x normal)",
                confidence="medium",
                magnitude=min(spike_factor * 10, 100),
                direction="NEUTRAL",
                detected_at=datetime.now(),
                alpha_score=spike_factor * 10,
            )
        return None

    def detect_orderbook_imbalance(
        self, market: Market, orderbook: Optional[OrderBook]
    ) -> Optional[Edge]:
        """Detect bid/ask imbalance + whale activity in orderbook"""
        if not orderbook or not orderbook.bids or not orderbook.asks:
            return None

        # Sum up volume on each side (top 5 levels)
        bid_volume = sum(b.size for b in orderbook.bids[:5])
        ask_volume = sum(a.size for a in orderbook.asks[:5])

        if bid_volume == 0 or ask_volume == 0:
            return None

        ratio = bid_volume / ask_volume

        # Detect whale orders ($5k+)
        whale_bids = [b for b in orderbook.bids if b.size * b.price >= self.whale_order_size]
        whale_asks = [a for a in orderbook.asks if a.size * a.price >= self.whale_order_size]

        whale_bid_vol = sum(b.size * b.price for b in whale_bids)
        whale_ask_vol = sum(a.size * a.price for a in whale_asks)

        # Smart money signal: whale clustering
        if len(whale_bids) >= self.whale_cluster_threshold and whale_bid_vol > whale_ask_vol * 2:
            alpha = min(whale_bid_vol / 1000 + len(whale_bids) * 10, 100)
            return Edge(
                market=market,
                edge_type="whale_activity",
                description=f"smart money loading! {len(whale_bids)} whale bids (${whale_bid_vol:,.0f})",
                confidence="high",
                magnitude=min(len(whale_bids) * 20 + ratio * 10, 100),
                direction="YES",
                detected_at=datetime.now(),
                alpha_score=alpha,
            )

        if len(whale_asks) >= self.whale_cluster_threshold and whale_ask_vol > whale_bid_vol * 2:
            alpha = min(whale_ask_vol / 1000 + len(whale_asks) * 10, 100)
            return Edge(
                market=market,
                edge_type="whale_activity",
                description=f"smart money exiting! {len(whale_asks)} whale asks (${whale_ask_vol:,.0f})",
                confidence="high",
                magnitude=min(len(whale_asks) * 20 + (1/ratio) * 10, 100),
                direction="NO",
                detected_at=datetime.now(),
                alpha_score=alpha,
            )

        # Standard imbalance detection
        # Strong buy pressure: bids >> asks
        if ratio > 3.0:
            alpha = min(ratio * 15 + (market.liquidity / 10000), 100)
            return Edge(
                market=market,
                edge_type="orderbook_imbalance",
                description=f"heavy buy pressure - {ratio:.1f}x more bids than asks",
                confidence="high" if ratio > 5 else "medium",
                magnitude=min(ratio * 15, 100),
                direction="YES",
                detected_at=datetime.now(),
                alpha_score=alpha,
            )

        # Strong sell pressure: asks >> bids
        if ratio < 0.33:
            inv_ratio = 1 / ratio
            alpha = min(inv_ratio * 15 + (market.liquidity / 10000), 100)
            return Edge(
                market=market,
                edge_type="orderbook_imbalance",
                description=f"heavy sell pressure - {inv_ratio:.1f}x more asks than bids",
                confidence="high" if ratio < 0.2 else "medium",
                magnitude=min(inv_ratio * 15, 100),
                direction="NO",
                detected_at=datetime.now(),
                alpha_score=alpha,
            )

        return None

    async def scan_market(
        self, market: Market, client: PolymarketClient
    ) -> list[Edge]:
        """Run all detection strategies on a single market"""
        edges = []

        # Skip low-volume markets
        if market.volume_24h < self.min_volume_usd:
            return edges

        # Update price tracking
        self.update_price(market)

        # Run detection strategies (priority order)
        arb = self.detect_arbitrage(market)
        if arb:
            edges.append(arb)

        movement = self.detect_odds_movement(market)
        if movement:
            edges.append(movement)

        volume = self.detect_volume_spike(market)
        if volume:
            edges.append(volume)

        # Fetch orderbook for imbalance + whale detection
        orderbook = await client.get_orderbook(market.yes_token_id)
        imbalance = self.detect_orderbook_imbalance(market, orderbook)
        if imbalance:
            edges.append(imbalance)

        return edges

    async def scan_all_markets(
        self, client: PolymarketClient, limit: int = 50
    ) -> list[Edge]:
        """Scan top markets for edges, sorted by alpha score"""
        all_edges = []

        markets = await client.get_markets(limit=limit)

        for market in markets:
            edges = await self.scan_market(market, client)
            all_edges.extend(edges)

        # Sort by alpha score (best signals first), fallback to magnitude
        all_edges.sort(key=lambda e: (e.alpha_score, e.magnitude), reverse=True)

        return all_edges
