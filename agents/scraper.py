"""
Web scraper for extracting REAL rental prices from websites.
This module handles actual website navigation, form filling, and price extraction.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
from browser.stealth_browser import StealthBrowser

logger = logging.getLogger("rental_agent.scraper")


class RentalScraper:
    """Scrapes REAL prices from rental truck websites."""
    
    async def scrape_uhaul(self, pickup: str, dropoff: str, pickup_date: str) -> Optional[Dict[str, Any]]:
        """Scrape U-Haul prices."""
        browser = StealthBrowser(headless=True)
        try:
            page = await browser.launch()
            if not page:
                logger.error("U-Haul: Browser launch failed")
                return None
            
            if not await browser.navigate("https://www.uhaul.com"):
                logger.error("U-Haul: Navigation failed")
                return None
            
            # Fill pickup location
            try:
                await browser.human_type('input[placeholder*="Pickup"]', pickup)
                await asyncio.sleep(1)
            except:
                logger.warning("U-Haul: Could not fill pickup location")
                return None
            
            # Fill dropoff location
            try:
                await browser.human_type('input[placeholder*="Drop-off"]', dropoff)
                await asyncio.sleep(1)
            except:
                logger.warning("U-Haul: Could not fill dropoff location")
                return None
            
            # Click search
            try:
                await browser.human_click('button[type="submit"]')
                await asyncio.sleep(5)  # Wait for results
            except:
                logger.warning("U-Haul: Could not click search")
                return None
            
            # Extract prices using Groq Vision
            screenshot = await browser.screenshot("uhaul_results")
            if not screenshot:
                logger.warning("U-Haul: Could not capture screenshot")
                return None
            
            # Parse prices from screenshot
            prices = await self._extract_prices_from_screenshot(screenshot, "U-Haul", pickup, dropoff)
            return prices
            
        except Exception as e:
            logger.error(f"U-Haul scraping error: {e}")
            return None
        finally:
            await browser.close()
    
    async def scrape_budget(self, pickup: str, dropoff: str, pickup_date: str) -> Optional[Dict[str, Any]]:
        """Scrape Budget Truck Rental prices."""
        browser = StealthBrowser(headless=True)
        try:
            page = await browser.launch()
            if not page:
                logger.error("Budget: Browser launch failed")
                return None
            
            if not await browser.navigate("https://www.budgettruck.com"):
                logger.error("Budget: Navigation failed")
                return None
            
            # Fill pickup location
            try:
                await browser.human_type('input[name*="pickup"]', pickup)
                await asyncio.sleep(1)
            except:
                logger.warning("Budget: Could not fill pickup location")
                return None
            
            # Fill dropoff location
            try:
                await browser.human_type('input[name*="dropoff"]', dropoff)
                await asyncio.sleep(1)
            except:
                logger.warning("Budget: Could not fill dropoff location")
                return None
            
            # Click search
            try:
                await browser.human_click('button[class*="search"]')
                await asyncio.sleep(5)
            except:
                logger.warning("Budget: Could not click search")
                return None
            
            screenshot = await browser.screenshot("budget_results")
            if not screenshot:
                logger.warning("Budget: Could not capture screenshot")
                return None
            
            prices = await self._extract_prices_from_screenshot(screenshot, "Budget Truck Rental", pickup, dropoff)
            return prices
            
        except Exception as e:
            logger.error(f"Budget scraping error: {e}")
            return None
        finally:
            await browser.close()
    
    async def scrape_penske(self, pickup: str, dropoff: str, pickup_date: str) -> Optional[Dict[str, Any]]:
        """Scrape Penske prices."""
        browser = StealthBrowser(headless=True)
        try:
            page = await browser.launch()
            if not page:
                logger.error("Penske: Browser launch failed")
                return None
            
            if not await browser.navigate("https://www.pensketruckrental.com"):
                logger.error("Penske: Navigation failed")
                return None
            
            # Fill pickup location
            try:
                await browser.human_type('input[id*="pickup"]', pickup)
                await asyncio.sleep(1)
            except:
                logger.warning("Penske: Could not fill pickup location")
                return None
            
            # Fill dropoff location
            try:
                await browser.human_type('input[id*="dropoff"]', dropoff)
                await asyncio.sleep(1)
            except:
                logger.warning("Penske: Could not fill dropoff location")
                return None
            
            # Click search
            try:
                await browser.human_click('button[type="submit"]')
                await asyncio.sleep(5)
            except:
                logger.warning("Penske: Could not click search")
                return None
            
            screenshot = await browser.screenshot("penske_results")
            if not screenshot:
                logger.warning("Penske: Could not capture screenshot")
                return None
            
            prices = await self._extract_prices_from_screenshot(screenshot, "Penske Truck Rental", pickup, dropoff)
            return prices
            
        except Exception as e:
            logger.error(f"Penske scraping error: {e}")
            return None
        finally:
            await browser.close()
    
    async def scrape_ryder(self, pickup: str, dropoff: str, pickup_date: str) -> Optional[Dict[str, Any]]:
        """Scrape Ryder prices."""
        browser = StealthBrowser(headless=True)
        try:
            page = await browser.launch()
            if not page:
                logger.error("Ryder: Browser launch failed")
                return None
            
            if not await browser.navigate("https://www.ryder.com/truck-rental"):
                logger.error("Ryder: Navigation failed")
                return None
            
            # Fill pickup location
            try:
                await browser.human_type('input[name="pickUp"]', pickup)
                await asyncio.sleep(1)
            except:
                logger.warning("Ryder: Could not fill pickup location")
                return None
            
            # Fill dropoff location
            try:
                await browser.human_type('input[name="dropOff"]', dropoff)
                await asyncio.sleep(1)
            except:
                logger.warning("Ryder: Could not fill dropoff location")
                return None
            
            # Click search
            try:
                await browser.human_click('button[name="search"]')
                await asyncio.sleep(5)
            except:
                logger.warning("Ryder: Could not click search")
                return None
            
            screenshot = await browser.screenshot("ryder_results")
            if not screenshot:
                logger.warning("Ryder: Could not capture screenshot")
                return None
            
            prices = await self._extract_prices_from_screenshot(screenshot, "Ryder System", pickup, dropoff)
            return prices
            
        except Exception as e:
            logger.error(f"Ryder scraping error: {e}")
            return None
        finally:
            await browser.close()
    
    async def scrape_enterprise(self, pickup: str, dropoff: str, pickup_date: str) -> Optional[Dict[str, Any]]:
        """Scrape Enterprise prices."""
        browser = StealthBrowser(headless=True)
        try:
            page = await browser.launch()
            if not page:
                logger.error("Enterprise: Browser launch failed")
                return None
            
            if not await browser.navigate("https://www.enterprisetrucks.com"):
                logger.error("Enterprise: Navigation failed")
                return None
            
            # Fill pickup location
            try:
                await browser.human_type('input[id*="pickupLocation"]', pickup)
                await asyncio.sleep(1)
            except:
                logger.warning("Enterprise: Could not fill pickup location")
                return None
            
            # Fill dropoff location
            try:
                await browser.human_type('input[id*="returnLocation"]', dropoff)
                await asyncio.sleep(1)
            except:
                logger.warning("Enterprise: Could not fill dropoff location")
                return None
            
            # Click search
            try:
                await browser.human_click('button[id*="search"]')
                await asyncio.sleep(5)
            except:
                logger.warning("Enterprise: Could not click search")
                return None
            
            screenshot = await browser.screenshot("enterprise_results")
            if not screenshot:
                logger.warning("Enterprise: Could not capture screenshot")
                return None
            
            prices = await self._extract_prices_from_screenshot(screenshot, "Enterprise Truck Rental", pickup, dropoff)
            return prices
            
        except Exception as e:
            logger.error(f"Enterprise scraping error: {e}")
            return None
        finally:
            await browser.close()
    
    async def _extract_prices_from_screenshot(
        self, screenshot_data: bytes, provider: str, pickup: str, dropoff: str
    ) -> Optional[Dict[str, Any]]:
        """
        Extract prices from website screenshot using Groq Vision.
        IMPORTANT: This should extract ALL truck options and calculate average.
        """
        import base64
        import httpx
        import json
        import os
        
        GROQ_API_KEY = os.getenv("GROQ_API_KEY")
        if not GROQ_API_KEY:
            logger.error(f"{provider}: No Groq API key")
            return None
        
        screenshot_b64 = base64.b64encode(screenshot_data).decode("utf-8")
        
        prompt = f"""You are analyzing a {provider} truck rental pricing page screenshot.

TASK: Extract ALL truck options and prices shown on this page.

Return ONLY valid JSON with this structure:
{{
  "truck_options": [
    {{"class": "10ft Truck", "daily_rate": 45.99, "estimated_total": 229.95}},
    {{"class": "16ft Truck", "daily_rate": 59.99, "estimated_total": 299.95}},
    {{"class": "26ft Truck", "daily_rate": 79.99, "estimated_total": 399.95}}
  ],
  "average_daily_rate": 61.99,
  "average_total": 309.95,
  "confidence": 0.95,
  "raw_text": "exact text from screenshot where you found prices"
}}

RULES:
- Extract EVERY truck option visible (don't skip any)
- Calculate averages: average_daily_rate = sum(daily_rates) / count
- Calculate average_total = sum(totals) / count  
- If no prices found, return empty truck_options array
- confidence: 0.9-1.0 if clear, 0.7-0.9 if partial, below 0.5 if very unclear
- Return ONLY JSON, no markdown
- Include raw_text: quote the exact prices you saw"""
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {GROQ_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "llama-3.2-90b-vision-preview",
                        "messages": [
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": prompt},
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": f"data:image/png;base64,{screenshot_b64}",
                                            "detail": "high"
                                        }
                                    }
                                ]
                            }
                        ],
                        "max_tokens": 1024,
                        "temperature": 0.1,
                    },
                )
                
                if response.status_code != 200:
                    logger.error(f"{provider}: Groq API error {response.status_code}")
                    return None
                
                data = response.json()
                content = data["choices"][0]["message"]["content"].strip()
                
                # Remove markdown if present
                if content.startswith("```"):
                    content = content.split("```")[1]
                    if content.startswith("json"):
                        content = content[4:]
                    content = content.strip()
                
                parsed = json.loads(content)
                
                # Validate we have real data
                if not parsed.get("truck_options") or len(parsed["truck_options"]) == 0:
                    logger.warning(f"{provider}: No truck options found in screenshot")
                    return None
                
                if parsed.get("average_total") is None or parsed["average_total"] <= 0:
                    logger.warning(f"{provider}: Invalid price data")
                    return None
                
                # Return formatted result with ALL truck options
                return {
                    "provider_name": provider,
                    "pickup_location": pickup,
                    "dropoff_location": dropoff,
                    "extracted_at": datetime.utcnow().isoformat(),
                    "total_price": parsed["average_total"],
                    "daily_rate": parsed["average_daily_rate"],
                    "truck_options": parsed["truck_options"],  # All options for reference
                    "confidence_score": parsed.get("confidence", 0.8),
                    "raw_text": parsed.get("raw_text", ""),
                    "availability": True,
                    "currency": "USD",
                    "mileage_fee": None,  # Calculated from average, not per-mile
                    "vehicle_class": "Mixed Fleet Average",  # Average of all options
                }
                
        except json.JSONDecodeError as e:
            logger.error(f"{provider}: JSON parse error: {e}")
            return None
        except Exception as e:
            logger.error(f"{provider}: Groq Vision error: {e}")
            return None
    
    async def scrape(self, provider_name: str, pickup: str, dropoff: str, pickup_date: str) -> Optional[Dict[str, Any]]:
        """Main scrape method - routes to specific provider scraper."""
        logger.info(f"🔍 Scraping {provider_name}: {pickup} → {dropoff}")
        
        # Route to provider-specific scraper
        if "U-Haul" in provider_name:
            return await self.scrape_uhaul(pickup, dropoff, pickup_date)
        elif "Budget" in provider_name:
            return await self.scrape_budget(pickup, dropoff, pickup_date)
        elif "Penske" in provider_name:
            return await self.scrape_penske(pickup, dropoff, pickup_date)
        elif "Enterprise" in provider_name:
            return await self.scrape_enterprise(pickup, dropoff, pickup_date)
        elif "Ryder" in provider_name:
            return await self.scrape_ryder(pickup, dropoff, pickup_date)
        else:
            # For other providers, log that we don't have specific support yet
            logger.warning(f"⚠️  No scraper implemented for {provider_name} yet")
            return None
