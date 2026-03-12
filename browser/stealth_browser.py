"""
Stealth Browser — Playwright automation with anti-detection measures
"""

import asyncio
import logging
import random
from pathlib import Path
from typing import Optional

logger = logging.getLogger("rental_agent.browser")

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

VIEWPORTS = [
    {"width": 1920, "height": 1080},
    {"width": 1440, "height": 900},
    {"width": 1366, "height": 768},
    {"width": 1280, "height": 800},
]


class StealthBrowser:
    """
    Playwright browser with stealth configuration.
    Mimics human browsing behavior.
    """

    def __init__(self, headless: bool = True):
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.screenshot_dir = Path("logs/screenshots")
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)

    async def launch(self):
        """Launch browser with stealth settings."""
        try:
            from playwright.async_api import async_playwright
            self.playwright = await async_playwright().start()

            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage",
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-infobars",
                    "--window-position=0,0",
                    "--ignore-certifcate-errors",
                    "--ignore-certifcate-errors-spki-list",
                ],
            )

            viewport = random.choice(VIEWPORTS)
            user_agent = random.choice(USER_AGENTS)

            self.context = await self.browser.new_context(
                viewport=viewport,
                user_agent=user_agent,
                locale="en-US",
                timezone_id="America/New_York",
                permissions=["geolocation"],
                extra_http_headers={
                    "Accept-Language": "en-US,en;q=0.9",
                    "Accept-Encoding": "gzip, deflate, br",
                },
            )

            # Inject stealth JS to mask automation
            await self.context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3] });
                window.chrome = { runtime: {} };
            """)

            self.page = await self.context.new_page()
            logger.info(f"Browser launched with UA: {user_agent[:50]}...")
            return self.page

        except ImportError:
            logger.warning("Playwright not installed. Browser automation disabled.")
            return None

    async def navigate(self, url: str, wait_for: str = "networkidle"):
        """Navigate to URL with human-like behavior."""
        if not self.page:
            logger.warning("No page available")
            return False

        try:
            # Random delay before navigation
            await asyncio.sleep(random.uniform(0.5, 2.0))
            await self.page.goto(url, wait_until=wait_for, timeout=30000)

            # Simulate reading time
            await self._simulate_human_scroll()
            return True
        except Exception as e:
            logger.error(f"Navigation failed: {e}")
            return False

    async def _simulate_human_scroll(self):
        """Scroll page like a human reader."""
        if not self.page:
            return
        try:
            scroll_amount = random.randint(200, 600)
            await self.page.evaluate(f"window.scrollBy(0, {scroll_amount})")
            await asyncio.sleep(random.uniform(0.3, 1.2))
            await self.page.evaluate(f"window.scrollBy(0, -{scroll_amount // 2})")
        except Exception:
            pass

    async def human_click(self, selector: str):
        """Click element with human-like mouse movement."""
        if not self.page:
            return
        try:
            element = await self.page.wait_for_selector(selector, timeout=10000)
            box = await element.bounding_box()
            if box:
                # Click slightly off-center for human feel
                x = box["x"] + box["width"] * random.uniform(0.3, 0.7)
                y = box["y"] + box["height"] * random.uniform(0.3, 0.7)
                await self.page.mouse.move(x, y)
                await asyncio.sleep(random.uniform(0.1, 0.3))
                await self.page.mouse.click(x, y)
        except Exception as e:
            logger.error(f"Click failed on {selector}: {e}")

    async def human_type(self, selector: str, text: str):
        """Type text with human-like delays."""
        if not self.page:
            return
        try:
            await self.page.click(selector)
            for char in text:
                await self.page.keyboard.type(char)
                await asyncio.sleep(random.uniform(0.05, 0.18))
        except Exception as e:
            logger.error(f"Type failed on {selector}: {e}")

    async def screenshot(self, name: str = "screenshot") -> Optional[bytes]:
        """Capture full-page screenshot."""
        if not self.page:
            return None
        try:
            path = self.screenshot_dir / f"{name}_{int(asyncio.get_event_loop().time())}.png"
            data = await self.page.screenshot(full_page=True, path=str(path))
            logger.info(f"Screenshot saved: {path}")
            return data
        except Exception as e:
            logger.error(f"Screenshot failed: {e}")
            return None

    async def close(self):
        """Clean up browser resources."""
        try:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
        except Exception as e:
            logger.error(f"Browser close error: {e}")
