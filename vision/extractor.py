"""
Vision Extractor — Groq Vision API integration for price extraction
"""

import base64
import json
import logging
import os
from pathlib import Path
from typing import Dict, Optional

import httpx

logger = logging.getLogger("rental_agent.vision")

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_BASE_URL = "https://api.groq.com/openai/v1/chat/completions"

# Use Groq's vision-capable model
MODEL = "llama-3.2-90b-vision-preview"

SYSTEM_PROMPT = """You are a specialized pricing extraction AI.

Given a screenshot of a truck rental website, extract all visible pricing information.

Return ONLY this JSON structure with no preamble or markdown:
{
  "provider_name": "string",
  "vehicle_class": "string",
  "total_price": number or null,
  "daily_rate": number or null,
  "mileage_fee": number or null,
  "currency": "USD",
  "availability": true or false,
  "confidence_score": 0.0-1.0,
  "raw_text": "relevant price text found on page"
}

Extraction rules:
- Prefer the LOWEST total price if multiple vehicles shown
- total_price = full estimated trip cost
- daily_rate = per-day rate if shown separately
- mileage_fee = per-mile charge
- confidence_score = 0.95 if price clearly visible, 0.5 if inferred
- If page shows "unavailable" or no trucks available: availability = false
"""


async def extract_price_from_screenshot(
    screenshot_bytes: bytes,
    provider_name: str,
    context: str = "",
) -> Optional[Dict]:
    """
    Send a screenshot to Groq Vision and extract pricing data.

    Args:
        screenshot_bytes: Raw PNG/JPEG bytes of the page screenshot
        provider_name: Name of the rental company (for context)
        context: Additional context (search params, etc.)

    Returns:
        Parsed dict with pricing data, or None on failure
    """
    if not GROQ_API_KEY:
        logger.warning("GROQ_API_KEY not set — returning None")
        return None

    # Encode screenshot as base64
    img_b64 = base64.standard_b64encode(screenshot_bytes).decode("utf-8")

    user_content = [
        {
            "type": "image_url",
            "image_url": {
                "url": f"data:image/png;base64,{img_b64}",
                "detail": "high",
            },
        },
        {
            "type": "text",
            "text": f"This is a screenshot from {provider_name}'s rental website. {context}\n\nExtract the pricing data as JSON.",
        },
    ]

    try:
        async with httpx.AsyncClient(timeout=40.0) as client:
            response = await client.post(
                GROQ_BASE_URL,
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": MODEL,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_content},
                    ],
                    "max_tokens": 512,
                    "temperature": 0.05,
                },
            )

            if response.status_code != 200:
                logger.error(f"Groq Vision API error {response.status_code}: {response.text[:300]}")
                return None

            data = response.json()
            raw = data["choices"][0]["message"]["content"].strip()

            # Strip markdown fences if present
            if raw.startswith("```"):
                parts = raw.split("```")
                raw = parts[1] if len(parts) > 1 else raw
                if raw.startswith("json"):
                    raw = raw[4:]

            result = json.loads(raw.strip())
            result["provider_name"] = provider_name  # Ensure correct provider
            logger.info(f"[{provider_name}] Extracted: {result.get('total_price')} {result.get('currency')}")
            return result

    except json.JSONDecodeError as e:
        logger.error(f"[{provider_name}] JSON parse error: {e}")
        return None
    except Exception as e:
        logger.error(f"[{provider_name}] Vision extraction failed: {e}")
        return None


async def extract_price_from_text(
    page_text: str,
    provider_name: str,
    pickup: str,
    dropoff: str,
    date: str,
) -> Optional[Dict]:
    """
    Text-only extraction via Groq (fallback when screenshot not available).
    Uses chat completion instead of vision.
    """
    if not GROQ_API_KEY:
        return None

    prompt = f"""
Rental provider: {provider_name}
Search: {pickup} → {dropoff} on {date}

Page text excerpt:
{page_text[:3000]}

Extract pricing data and return JSON only.
"""

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(
                GROQ_BASE_URL,
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "llama-3.3-70b-versatile",  # Text model for DOM fallback
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                    "max_tokens": 512,
                    "temperature": 0.05,
                },
            )

            if response.status_code != 200:
                return None

            data = response.json()
            raw = data["choices"][0]["message"]["content"].strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]

            return json.loads(raw.strip())

    except Exception as e:
        logger.error(f"Text extraction failed for {provider_name}: {e}")
        return None
