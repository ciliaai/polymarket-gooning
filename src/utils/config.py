"""
Configuration Management

Loads and validates configuration from environment variables.
"""

import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv


@dataclass
class Config:
    """Application configuration"""

    # Polymarket
    polymarket_private_key: Optional[str]
    polymarket_funder_address: Optional[str]

    # Grok
    grok_api_key: str

    # Twitter
    twitter_api_key: str
    twitter_api_secret: str
    twitter_access_token: str
    twitter_access_secret: str

    # Proxy
    use_proxy: bool
    proxy_host: Optional[str]
    proxy_port: Optional[str]
    proxy_user: Optional[str]
    proxy_pass: Optional[str]

    # Detection settings
    check_interval_seconds: int
    min_odds_change_percent: float
    min_volume_usd: float

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment"""
        load_dotenv()

        return cls(
            # Polymarket
            polymarket_private_key=os.getenv("POLYMARKET_PRIVATE_KEY"),
            polymarket_funder_address=os.getenv("POLYMARKET_FUNDER_ADDRESS"),

            # Grok
            grok_api_key=os.getenv("GROK_API_KEY", ""),

            # Twitter
            twitter_api_key=os.getenv("TWITTER_API_KEY", ""),
            twitter_api_secret=os.getenv("TWITTER_API_SECRET", ""),
            twitter_access_token=os.getenv("TWITTER_ACCESS_TOKEN", ""),
            twitter_access_secret=os.getenv("TWITTER_ACCESS_SECRET", ""),

            # Proxy
            use_proxy=os.getenv("USE_PROXY", "false").lower() == "true",
            proxy_host=os.getenv("PROXY_HOST"),
            proxy_port=os.getenv("PROXY_PORT"),
            proxy_user=os.getenv("PROXY_USER"),
            proxy_pass=os.getenv("PROXY_PASS"),

            # Detection
            check_interval_seconds=int(os.getenv("CHECK_INTERVAL_SECONDS", "180")),
            min_odds_change_percent=float(os.getenv("MIN_ODDS_CHANGE_PERCENT", "5")),
            min_volume_usd=float(os.getenv("MIN_VOLUME_USD", "1000")),
        )

    def get_proxy_url(self) -> Optional[str]:
        """Build proxy URL if enabled"""
        if not self.use_proxy:
            return None

        if all([self.proxy_host, self.proxy_port, self.proxy_user, self.proxy_pass]):
            return f"http://{self.proxy_user}:{self.proxy_pass}@{self.proxy_host}:{self.proxy_port}"

        return None

    def validate(self) -> list[str]:
        """Validate configuration, return list of errors"""
        errors = []

        if not self.grok_api_key:
            errors.append("GROK_API_KEY is required")

        if not self.twitter_api_key:
            errors.append("TWITTER_API_KEY is required")

        if not self.twitter_api_secret:
            errors.append("TWITTER_API_SECRET is required")

        if not self.twitter_access_token:
            errors.append("TWITTER_ACCESS_TOKEN is required")

        if not self.twitter_access_secret:
            errors.append("TWITTER_ACCESS_SECRET is required")

        return errors
