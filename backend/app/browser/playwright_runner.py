import os
from typing import Optional, List, Dict, Any
from urllib.parse import urlparse
from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Playwright
from backend.app.config import settings

class SafetyBoundaryViolation(Exception):
    """Raised when an agent attempts to navigate or interact outside authorized origin boundaries."""
    pass

class PlaywrightBrowserManager:
    """Manages browser lifecycle, device emulation, and origin boundary enforcement."""

    def __init__(self):
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None

    async def initialize(self):
        if not self._playwright:
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=settings.HEADLESS_BROWSER,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu"
                ]
            )

    async def shutdown(self):
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None

    @staticmethod
    def get_origin(url: str) -> str:
        parsed = urlparse(url)
        netloc = parsed.netloc
        scheme = parsed.scheme or "http"
        return f"{scheme}://{netloc}".lower()

    @classmethod
    def is_origin_allowed(cls, target_url: str, allowed_origins: List[str]) -> bool:
        if not settings.ENFORCE_ALLOWED_ORIGINS:
            return True
        if not allowed_origins:
            return True

        target_origin = cls.get_origin(target_url)
        normalized_allowed = [cls.get_origin(ao) for ao in allowed_origins]

        # Allow matching host and localhost / 127.0.0.1 equivalence
        for allowed in normalized_allowed:
            if target_origin == allowed:
                return True
            # Allow port-matching localhost vs 127.0.0.1
            if ("localhost" in target_origin or "127.0.0.1" in target_origin) and \
               ("localhost" in allowed or "127.0.0.1" in allowed):
                port_target = urlparse(target_url).port
                port_allowed = urlparse(allowed).port
                if port_target == port_allowed:
                    return True
        return False

    async def create_user_context(
        self,
        device_profile: Dict[str, Any],
        network_profile: Dict[str, Any],
        allowed_origins: List[str]
    ) -> BrowserContext:
        await self.initialize()

        viewport = {
            "width": device_profile.get("viewport_width", 1280),
            "height": device_profile.get("viewport_height", 800)
        }
        user_agent = device_profile.get("user_agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) SyntheticHuman/1.0")

        context = await self._browser.new_context(
            viewport=viewport,
            user_agent=user_agent,
            ignore_https_errors=True
        )

        # Enforce route filtering to block unauthorized foreign domains
        async def route_interceptor(route):
            request_url = route.request.url
            # Allow standard data URIs and inline assets
            if request_url.startswith("data:") or request_url.startswith("blob:"):
                await route.continue_()
                return

            req_origin = self.get_origin(request_url)
            # Check if navigation request violates origin
            if route.request.is_navigation_request():
                if not self.is_origin_allowed(request_url, allowed_origins):
                    # Abort unauthorized navigation
                    await route.abort("accessdenied")
                    return
            await route.continue_()

        if allowed_origins:
            await context.route("**/*", route_interceptor)

        return context

browser_manager = PlaywrightBrowserManager()
