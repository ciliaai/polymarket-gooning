"""
Grok/xAI Image Generator
Creates Venezuelan beauty reaction images for trading signals
"""

import httpx
import os
import base64
from typing import Optional
from edge_detector import Edge


class GrokImageGenerator:
    API_URL = "https://api.x.ai/v1/images/generations"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GROK_API_KEY")
        if not self.api_key:
            raise ValueError("GROK_API_KEY not provided")

    def _build_prompt(self, edge: Edge) -> str:
        """Generate appropriate Venezuelan beauty prompt based on edge type"""

        # Base style - young hot Venezuelan girl
        base_style = "extremely attractive young Venezuelan woman in her early 20s, stunning latina beauty, hot, sexy, long dark hair, tan skin, gorgeous face, model looks, revealing outfit showing cleavage, busty, fit curvy body, instagram model aesthetic, vibrant colors, professional photography, influencer vibes"

        # Reaction based on edge type and direction
        if edge.edge_type == "arbitrage":
            reaction = "excited young latina celebrating with money, party vibes, champagne, showing off"
            mood = "ecstatic, winning, hot girl energy"

        elif edge.edge_type == "odds_movement":
            if edge.direction == "YES":
                reaction = "confident young Venezuelan girl pointing up, seductive smirk, boss babe energy"
                mood = "confident, bullish, flirty"
            else:
                reaction = "skeptical hot latina with raised eyebrow, pouty lips, not impressed"
                mood = "cautious, bearish, sassy"

        elif edge.edge_type == "volume_spike":
            reaction = "surprised gorgeous young latina with wide eyes, dramatic expression, hand on chest"
            mood = "surprised, alert, amazed"

        elif edge.edge_type == "orderbook_imbalance":
            if edge.direction == "YES":
                reaction = "knowing hot girl with sly smile, finger on lips shushing, playful secretive"
                mood = "clever, knowing, seductive"
            else:
                reaction = "concerned cute latina biting lip, worried but still pretty"
                mood = "worried, cautious, soft"

        else:
            reaction = "curious young Venezuelan beauty with questioning expression, head tilt, intrigued"
            mood = "curious, flirty"

        # Confidence affects intensity
        if edge.confidence == "high":
            intensity = "very expressive, dramatic lighting, emphasized emotions, bold"
        elif edge.confidence == "medium":
            intensity = "moderately expressive, warm lighting"
        else:
            intensity = "subtle expression, soft mood"

        prompt = f"{reaction}, {mood}, {intensity}, {base_style}, financial theme, luxury aesthetic"

        return prompt

    async def generate_image(self, edge: Edge) -> Optional[bytes]:
        """Generate a hot Venezuelan reaction image for the given edge"""
        prompt = self._build_prompt(edge)

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

                # Extract image (could be URL or base64)
                if data.get("data") and len(data["data"]) > 0:
                    item = data["data"][0]

                    # Check for base64
                    if item.get("b64_json"):
                        return base64.b64decode(item["b64_json"])

                    # Check for URL - download it
                    if item.get("url"):
                        img_resp = await client.get(item["url"])
                        img_resp.raise_for_status()
                        return img_resp.content

                return None

            except httpx.HTTPStatusError as e:
                print(f"Grok API error: {e.response.status_code} - {e.response.text[:200]}")
                return None
            except Exception as e:
                print(f"Image generation failed: {e}")
                return None

    async def generate_and_save(self, edge: Edge, output_path: str) -> bool:
        """Generate image and save to file"""
        image_bytes = await self.generate_image(edge)

        if image_bytes:
            with open(output_path, "wb") as f:
                f.write(image_bytes)
            return True

        return False
