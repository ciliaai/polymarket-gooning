"""
Polymarket API Client
Fetches markets, orderbooks, and price data via CLOB and Gamma APIs
"""

import httpx
import os
from typing import Optional
from dataclasses import dataclass


@dataclass
class Market:
    condition_id: str
    question: str
    slug: str
    event_slug: str  # Parent event slug for URL construction
    yes_price: float
    no_price: float
    volume_24h: float
    liquidity: float
    end_date: str
    category: str
    yes_token_id: str
    no_token_id: str

    def get_url(self) -> str:
        """Get the correct Polymarket URL for this market"""
        slug = self.event_slug or self.slug
        return f"polymarket.com/event/{slug}?tid={self.yes_token_id}"


@dataclass
class OrderBookLevel:
    price: float
    size: float


@dataclass
class OrderBook:
    token_id: str
    bids: list[OrderBookLevel]
    asks: list[OrderBookLevel]
    spread: float
    mid_price: float


class PolymarketClient:
    GAMMA_API = "https://gamma-api.polymarket.com"
    CLOB_API = "https://clob.polymarket.com"

    def __init__(self, proxy_url: Optional[str] = None):
        self.proxy_url = proxy_url
        self._client: Optional[httpx.AsyncClient] = None

    def _get_proxy_config(self) -> dict:
        if not self.proxy_url:
            return {}
        return {"proxy": self.proxy_url}

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=30.0,
                **self._get_proxy_config()
            )
        return self._client

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None

    async def get_markets(
        self,
        limit: int = 100,
        active: bool = True,
        min_price: float = 0.15,
        max_price: float = 0.85,
        min_year: int = 2026,
    ) -> list[Market]:
        """Fetch active markets from Gamma API with filters"""
        client = await self._get_client()

        params = {
            "limit": limit * 3,  # Fetch extra to filter
            "active": str(active).lower(),
            "closed": "false",
        }

        resp = await client.get(f"{self.GAMMA_API}/markets", params=params)
        resp.raise_for_status()
        data = resp.json()

        markets = []
        for m in data:
            try:
                # Parse token IDs from clobTokenIds field (can be list or JSON string)
                clob_token_ids = m.get("clobTokenIds", []) or []
                if isinstance(clob_token_ids, str):
                    import json
                    try:
                        clob_token_ids = json.loads(clob_token_ids)
                    except:
                        clob_token_ids = []
                yes_token_id = clob_token_ids[0] if len(clob_token_ids) > 0 else ""
                no_token_id = clob_token_ids[1] if len(clob_token_ids) > 1 else ""

                # Parse prices - can be list or JSON string
                outcome_prices = m.get("outcomePrices", [])
                if isinstance(outcome_prices, str):
                    import json
                    try:
                        outcome_prices = json.loads(outcome_prices)
                    except:
                        outcome_prices = []
                if isinstance(outcome_prices, list) and len(outcome_prices) >= 2:
                    yes_price = float(outcome_prices[0])
                    no_price = float(outcome_prices[1])
                else:
                    yes_price = 0.5
                    no_price = 0.5

                # Filter by price range (skip near-certain markets)
                if yes_price < min_price or yes_price > max_price:
                    continue

                # Filter by end date year
                end_date_str = m.get("endDate", "")
                if end_date_str:
                    try:
                        end_year = int(end_date_str[:4])
                        if end_year < min_year:
                            continue
                    except (ValueError, TypeError):
                        pass

                # Get event slug from events array (for grouped markets)
                events = m.get("events", [])
                event_slug = ""
                if events and len(events) > 0:
                    event_slug = events[0].get("slug", "")

                markets.append(Market(
                    condition_id=m.get("conditionId", ""),
                    question=m.get("question", ""),
                    slug=m.get("slug", ""),
                    event_slug=event_slug,
                    yes_price=yes_price,
                    no_price=no_price,
                    volume_24h=float(m.get("volume24hr", 0) or 0),
                    liquidity=float(m.get("liquidity", 0) or 0),
                    end_date=end_date_str,
                    category=m.get("category", ""),
                    yes_token_id=yes_token_id,
                    no_token_id=no_token_id,
                ))

                if len(markets) >= limit:
                    break

            except (ValueError, IndexError, KeyError) as e:
                continue

        return markets

    async def get_orderbook(self, token_id: str) -> Optional[OrderBook]:
        """Fetch orderbook for a specific token from CLOB API"""
        if not token_id:
            return None

        client = await self._get_client()

        try:
            resp = await client.get(f"{self.CLOB_API}/book", params={"token_id": token_id})
            resp.raise_for_status()
            data = resp.json()

            bids = [OrderBookLevel(float(b["price"]), float(b["size"]))
                    for b in data.get("bids", [])]
            asks = [OrderBookLevel(float(a["price"]), float(a["size"]))
                    for a in data.get("asks", [])]

            best_bid = bids[0].price if bids else 0
            best_ask = asks[0].price if asks else 1
            spread = best_ask - best_bid
            mid_price = (best_bid + best_ask) / 2

            return OrderBook(
                token_id=token_id,
                bids=bids,
                asks=asks,
                spread=spread,
                mid_price=mid_price,
            )
        except Exception:
            return None

    async def get_market_by_slug(self, slug: str) -> Optional[Market]:
        """Fetch a specific market by slug"""
        client = await self._get_client()

        resp = await client.get(f"{self.GAMMA_API}/markets", params={"slug": slug})
        resp.raise_for_status()
        data = resp.json()

        if not data:
            return None

        m = data[0]
        clob_token_ids = m.get("clobTokenIds", []) or []
        if isinstance(clob_token_ids, str):
            import json
            try:
                clob_token_ids = json.loads(clob_token_ids)
            except:
                clob_token_ids = []
        events = m.get("events", [])
        event_slug = events[0].get("slug", "") if events else ""

        return Market(
            condition_id=m.get("conditionId", ""),
            question=m.get("question", ""),
            slug=m.get("slug", ""),
            event_slug=event_slug,
            yes_price=float(m.get("outcomePrices", "[0.5,0.5]").strip("[]").split(",")[0]),
            no_price=float(m.get("outcomePrices", "[0.5,0.5]").strip("[]").split(",")[1]),
            volume_24h=float(m.get("volume24hr", 0) or 0),
            liquidity=float(m.get("liquidity", 0) or 0),
            end_date=m.get("endDate", ""),
            category=m.get("category", ""),
            yes_token_id=clob_token_ids[0] if len(clob_token_ids) > 0 else "",
            no_token_id=clob_token_ids[1] if len(clob_token_ids) > 1 else "",
        )

    async def get_price_history(self, token_id: str, interval: str = "1h") -> list[dict]:
        """Fetch price history for a token"""
        client = await self._get_client()

        try:
            resp = await client.get(
                f"{self.CLOB_API}/prices-history",
                params={"market": token_id, "interval": interval}
            )
            resp.raise_for_status()
            return resp.json().get("history", [])
        except Exception:
            return []


def build_proxy_url() -> Optional[str]:
    """Build proxy URL from environment variables"""
    # Check if proxy is enabled
    use_proxy = os.getenv("USE_PROXY", "true").lower() == "true"
    if not use_proxy:
        return None

    host = os.getenv("PROXY_HOST")
    port = os.getenv("PROXY_PORT")
    user = os.getenv("PROXY_USER")
    password = os.getenv("PROXY_PASS")

    if all([host, port, user, password]):
        return f"http://{user}:{password}@{host}:{port}"
    return None
