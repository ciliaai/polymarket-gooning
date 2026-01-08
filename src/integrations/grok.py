"""
Grok/xAI Image Generation Integration

Generates anime-style reaction images for trading signals.
"""

import httpx
import base64
import os
from typing import Optional
from dataclasses import dataclass


@dataclass
class ImageResult:
    success: bool
    image_bytes: Optional[bytes]
    prompt_used: str
    error: Optional[str]


class GrokImageGen:
    """
    Grok AI image generation for kawaii trading signals.

    Generates anime-style reaction images based on signal type
    and market sentiment.
    """

    API_URL = "https://api.x.ai/v1/images/generations"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GROK_API_KEY")
        if not self.api_key:
            raise ValueError("GROK_API_KEY not configured")

        self._generations = 0

    def _build_prompt(
        self,
        signal_type: str,
        direction: str,
        confidence: str,
    ) -> str:
        """Build image prompt based on signal characteristics"""
        base_style = "anime art, kawaii style, cute anime girl, vibrant colors, digital art, high quality"

        # Mood based on signal type
        moods = {
            "arbitrage": "excited, sparkling eyes, celebrating victory, money symbols",
            "odds_movement": "confident, determined, pointing forward" if direction == "YES" else "cautious, thoughtful, looking down",
            "volume_spike": "surprised, wide eyes, alert expression, crowd in background",
            "orderbook_imbalance": "knowing smile, detective pose, magnifying glass" if direction == "YES" else "worried, biting lip, concerned",
        }

        mood = moods.get(signal_type, "curious, analytical, looking at charts")

        # Intensity based on confidence
        intensity = {
            "high": "very expressive, dramatic lighting, emphasized emotions",
            "medium": "moderately expressive, soft lighting",
            "low": "subtle expression, calm mood",
        }

        prompt = f"{mood}, {intensity.get(confidence, 'neutral')}, {base_style}, trading theme"
        return prompt

    async def generate(
        self,
        signal_type: str,
        direction: str = "NEUTRAL",
        confidence: str = "medium",
    ) -> ImageResult:
        """Generate anime reaction image"""
        prompt = self._build_prompt(signal_type, direction, confidence)

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                resp = await client.post(
                    self.API_URL,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "grok-2-image-1212",
                        "prompt": prompt,
                        "n": 1,
                    },
                )
                resp.raise_for_status()
                data = resp.json()

                if data.get("data") and len(data["data"]) > 0:
                    b64_image = data["data"][0].get("b64_json")
                    if b64_image:
                        self._generations += 1
                        return ImageResult(
                            success=True,
                            image_bytes=base64.b64decode(b64_image),
                            prompt_used=prompt,
                            error=None,
                        )

                return ImageResult(
                    success=False,
                    image_bytes=None,
                    prompt_used=prompt,
                    error="No image in response",
                )

            except httpx.HTTPStatusError as e:
                return ImageResult(
                    success=False,
                    image_bytes=None,
                    prompt_used=prompt,
                    error=f"API error: {e.response.status_code}",
                )
            except Exception as e:
                return ImageResult(
                    success=False,
                    image_bytes=None,
                    prompt_used=prompt,
                    error=str(e),
                )

    async def generate_and_save(
        self,
        signal_type: str,
        output_path: str,
        direction: str = "NEUTRAL",
        confidence: str = "medium",
    ) -> bool:
        """Generate image and save to file"""
        result = await self.generate(signal_type, direction, confidence)

        if result.success and result.image_bytes:
            with open(output_path, "wb") as f:
                f.write(result.image_bytes)
            return True

        return False

    def get_stats(self) -> dict:
        return {
            "total_generations": self._generations,
        }
