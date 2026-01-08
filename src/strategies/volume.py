"""
Volume Anomaly Detection Strategy

Identifies unusual volume activity using statistical analysis.

Mathematical basis:
    z_score = (volume - mean) / std

    Signal triggered when z_score > threshold (default 2.5)

Volume spikes often precede significant price movements
as informed traders accumulate positions.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from collections import deque
import math


@dataclass
class VolumeSignal:
    market_id: str
    current_volume: float
    average_volume: float
    z_score: float
    spike_factor: float  # how many X average
    detected_at: datetime


class VolumeAnalyzer:
    """
    Detects volume anomalies using z-score analysis.

    Maintains rolling statistics of volume and flags
    significant deviations from normal activity.
    """

    def __init__(
        self,
        z_threshold: float = 2.5,
        min_history: int = 10,
        history_size: int = 50,
    ):
        self.z_threshold = z_threshold
        self.min_history = min_history
        self.history_size = history_size
        self.volume_history: dict[str, deque] = {}

    def update(
        self,
        market_id: str,
        volume_24h: float,
    ) -> Optional[VolumeSignal]:
        """
        Update volume history and detect anomalies.

        Args:
            market_id: Unique market identifier
            volume_24h: 24-hour trading volume

        Returns:
            VolumeSignal if anomaly detected
        """
        # Initialize history if needed
        if market_id not in self.volume_history:
            self.volume_history[market_id] = deque(maxlen=self.history_size)

        history = self.volume_history[market_id]
        history.append(volume_24h)

        # Need minimum history
        if len(history) < self.min_history:
            return None

        # Calculate statistics
        volumes = list(history)
        mean = sum(volumes) / len(volumes)

        if mean == 0:
            return None

        variance = sum((v - mean) ** 2 for v in volumes) / len(volumes)
        std = math.sqrt(variance)

        if std == 0:
            return None

        # Calculate z-score
        z_score = (volume_24h - mean) / std
        spike_factor = volume_24h / mean

        # Check threshold
        if z_score > self.z_threshold:
            return VolumeSignal(
                market_id=market_id,
                current_volume=volume_24h,
                average_volume=mean,
                z_score=z_score,
                spike_factor=spike_factor,
                detected_at=datetime.now(),
            )

        return None

    def get_stats(self, market_id: str) -> Optional[dict]:
        """Get volume statistics for a market"""
        if market_id not in self.volume_history:
            return None

        history = list(self.volume_history[market_id])
        if not history:
            return None

        mean = sum(history) / len(history)
        variance = sum((v - mean) ** 2 for v in history) / len(history)
        std = math.sqrt(variance)

        return {
            "mean": mean,
            "std": std,
            "min": min(history),
            "max": max(history),
            "history_length": len(history),
        }

    def get_z_score(
        self,
        market_id: str,
        volume: float,
    ) -> Optional[float]:
        """Calculate z-score for a given volume"""
        stats = self.get_stats(market_id)
        if not stats or stats["std"] == 0:
            return None

        return (volume - stats["mean"]) / stats["std"]
