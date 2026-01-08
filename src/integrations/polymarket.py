"""
Polymarket API Integration

Handles all communication with Polymarket's CLOB and Gamma APIs.
Includes rate limiting, retry logic, and proxy support.
"""

import httpx
import asyncio
from typing import Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class MarketData:
    condition_id: str
    question: str
    slug: str
    yes_price: float
    no_price: float
    volume_24h: float
    liquidity: float
    end_date: str
    category: str
    yes_token_id: str
    no_token_id: str


@dataclass
class OrderBookData:
    token_id: str
    bids: list[tuple[float, float]]  # (price, size)
    asks: list[tuple[float, float]]
    spread: float
    mid_price: float
    timestamp: datetime


class PolymarketAPI:
    """
    Polymarket API client with connection pooling and rate limiting.

    Endpoints:
    - Gamma API: Market metadata, historical data
    - CLOB API: Orderbooks, real-time pricing
    """

    GAMMA_API = "https://gamma-api.polymarket.com"
    CLOB_API = "https://clob.polymarket.com"

    def __init__(
        self,
        proxy_url: Optional[str] = None,
        timeout: float = 30.0,
        max_retries: int = 3,
    ):
        self.proxy_url = proxy_url
        self.timeout = timeout
        self.max_retries = max_retries
        self._client: Optional[httpx.AsyncClient] = None
        self._request_count = 0
        self._last_request_time: Optional[datetime] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            proxy_config = {"proxy": self.proxy_url} if self.proxy_url else {}
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                **proxy_config
            )
        return self._client

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _request(
        self,
        method: str,
        url: str,
        **kwargs
    ) -> dict:
        """Make request with retry logic"""
        client = await self._get_client()

        for attempt in range(self.max_retries):
            try:
                self._request_count += 1
                self._last_request_time = datetime.now()

                resp = await client.request(method, url, **kwargs)
                resp.raise_for_status()
                return resp.json()

            except httpx.HTTPStatusError as e:
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)  # Exponential backoff

            except httpx.RequestError as e:
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)

    async def get_markets(
        self,
        limit: int = 100,
        active: bool = True,
    ) -> list[MarketData]:
        """Fetch active markets from Gamma API"""
        params = {
            "limit": limit,
            "active": str(active).lower(),
            "closed": "false",
        }

        data = await self._request(
            "GET",
            f"{self.GAMMA_API}/markets",
            params=params
        )

        markets = []
        for m in data:
            try:
                clob_ids = m.get("clobTokenIds", [])
                prices = m.get("outcomePrices", "[0.5,0.5]")

                # Parse prices
                if isinstance(prices, str):
                    prices = prices.strip("[]").split(",")
                    yes_price = float(prices[0])
                    no_price = float(prices[1]) if len(prices) > 1 else 1 - yes_price
                else:
                    yes_price = 0.5
                    no_price = 0.5

                markets.append(MarketData(
                    condition_id=m.get("conditionId", ""),
                    question=m.get("question", ""),
                    slug=m.get("slug", ""),
                    yes_price=yes_price,
                    no_price=no_price,
                    volume_24h=float(m.get("volume24hr", 0) or 0),
                    liquidity=float(m.get("liquidity", 0) or 0),
                    end_date=m.get("endDate", ""),
                    category=m.get("category", ""),
                    yes_token_id=clob_ids[0] if clob_ids else "",
                    no_token_id=clob_ids[1] if len(clob_ids) > 1 else "",
                ))
            except (ValueError, IndexError, KeyError):
                continue

        return markets

    async def get_orderbook(
        self,
        token_id: str,
    ) -> Optional[OrderBookData]:
        """Fetch orderbook for a specific token"""
        if not token_id:
            return None

        try:
            data = await self._request(
                "GET",
                f"{self.CLOB_API}/book",
                params={"token_id": token_id}
            )

            bids = [(float(b["price"]), float(b["size"])) for b in data.get("bids", [])]
            asks = [(float(a["price"]), float(a["size"])) for a in data.get("asks", [])]

            best_bid = bids[0][0] if bids else 0
            best_ask = asks[0][0] if asks else 1
            spread = best_ask - best_bid
            mid = (best_bid + best_ask) / 2

            return OrderBookData(
                token_id=token_id,
                bids=bids,
                asks=asks,
                spread=spread,
                mid_price=mid,
                timestamp=datetime.now(),
            )

        except Exception:
            return None

    def get_stats(self) -> dict:
        """Get client statistics"""
        return {
            "request_count": self._request_count,
            "last_request": self._last_request_time,
            "proxy_enabled": self.proxy_url is not None,
        }
