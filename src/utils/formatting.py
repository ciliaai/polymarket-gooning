"""
Text Formatting Utilities

Helper functions for formatting prices, volumes, and text.
"""


def format_price(price: float, as_cents: bool = True) -> str:
    """Format price for display"""
    if as_cents:
        return f"{price * 100:.0f}c"
    return f"${price:.2f}"


def format_volume(volume: float) -> str:
    """Format volume with K/M suffixes"""
    if volume >= 1_000_000:
        return f"${volume/1_000_000:.1f}M"
    elif volume >= 1_000:
        return f"${volume/1_000:.1f}K"
    else:
        return f"${volume:.0f}"


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to max length with suffix"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def format_percent_change(change: float) -> str:
    """Format percentage change with sign"""
    sign = "+" if change > 0 else ""
    return f"{sign}{change * 100:.1f}%"


def format_risk_tier(tier: str) -> str:
    """Format risk tier for display"""
    tiers = {
        "low": "low risk",
        "medium": "med risk",
        "high": "high risk",
    }
    return tiers.get(tier, tier)


def format_signal_type(signal_type: str) -> str:
    """Format signal type for display"""
    return signal_type.replace("_", " ")


def build_polymarket_url(slug: str) -> str:
    """Build Polymarket event URL"""
    return f"polymarket.com/event/{slug}"


def format_digest_tweet(
    signal_count: int,
    top_market: str,
    direction: str,
    price: float,
    signal_type: str,
    risk_level: str,
    risk_breakdown: dict,
    slug: str,
) -> str:
    """Format an hourly digest tweet"""
    lines = [
        "hourly alpha digest~",
        "",
        f"detected {signal_count} signal{'s' if signal_count > 1 else ''}",
        "",
        f"top pick: {truncate_text(top_market, 100)}",
    ]

    if direction in ["YES", "NO"]:
        lines.append(f"{direction} @ {format_price(price)}")

    lines.extend([
        f"signal: {format_signal_type(signal_type)}",
        f"risk: {format_risk_tier(risk_level)}",
        "",
    ])

    # Add risk breakdown counts
    if risk_breakdown.get("low", 0) > 0:
        lines.append(f"low risk: {risk_breakdown['low']}")
    if risk_breakdown.get("medium", 0) > 0:
        lines.append(f"med risk: {risk_breakdown['medium']}")
    if risk_breakdown.get("high", 0) > 0:
        lines.append(f"high risk: {risk_breakdown['high']}")

    lines.extend([
        "",
        build_polymarket_url(slug),
    ])

    return "\n".join(lines)
