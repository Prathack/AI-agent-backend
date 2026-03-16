"""
Agent Orchestrator — coordinates real website scraping for rental prices
"""

import logging
from typing import Any, Callable, Dict, Optional

from agents.scraper import RentalScraper

logger = logging.getLogger("rental_agent.orchestrator")


class AgentOrchestrator:
    """Manages real website scraping for rental prices using RentalScraper."""

    def __init__(self):
        self.scraper = RentalScraper()

    async def run_agent(
        self,
        provider: Dict[str, Any],
        request: Any,
        status_callback: Optional[Callable] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Scrape REAL prices from provider website.
        Returns only actual data or None - NO FAKE DATA.
        """
        name = provider["name"]

        def log(status: str, msg: str):
            logger.info(f"[{name}] {msg}")
            if status_callback:
                status_callback(status, msg)

        try:
            log("starting", f"🔍 Fetching real prices from {name}")
            
            result = await self.scraper.scrape(
                provider_name=name,
                pickup=request.pickup_location,
                dropoff=request.dropoff_location,
                pickup_date=request.pickup_date,
            )
            
            if result:
                log("success", f"✅ Got real prices: ${result.get('total_price')} average (Confidence: {result.get('confidence_score', 0)*100:.0f}%)")
                return result
            else:
                log("failed", f"❌ Could not scrape real prices (website may be unavailable)")
                return None
                
        except Exception as e:
            log("error", f"❌ Error: {str(e)}")
            logger.error(f"[{name}] Exception: {e}", exc_info=True)
            return None
