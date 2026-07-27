from playwright.async_api import async_playwright, Browser, Page
from typing import Optional
import asyncio
import os

class BaseScraper:
    def __init__(self, platform: str, headless: bool = True):
        self.platform = platform
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.screenshot_dir = "./screenshots"
        os.makedirs(self.screenshot_dir, exist_ok=True)

    async def init(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=self.headless)
        context = await self.browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        )
        self.page = await context.new_page()

    async def close(self):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def screenshot(self, name: str) -> str:
        if not self.page:
            raise Exception("Page not initialized")
        path = f"{self.screenshot_dir}/{self.platform}-{name}.png"
        await self.page.screenshot(path=path, full_page=True)
        return path

    async def scrape(self, credentials: dict) -> dict:
        raise NotImplementedError

    async def retry(self, func, retries: int = 3):
        last_error = None
        for i in range(retries):
            try:
                return await func()
            except Exception as e:
                last_error = e
                if i < retries - 1:
                    await asyncio.sleep(1 * (i + 1))
        raise last_error
