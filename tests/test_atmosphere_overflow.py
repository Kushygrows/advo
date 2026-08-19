import asyncio
import os, pathlib

_PW_CHROMIUM_PATH = os.environ.get("PW_CHROMIUM_PATH")  # optional override; unset -> Playwright uses its own installed browser
from playwright.async_api import async_playwright

FILE = pathlib.Path(__file__).resolve().parent.parent.joinpath("advo.html").as_uri()
WIDTHS = [320, 375, 414, 768, 1024, 1920]

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(**({"executable_path": _PW_CHROMIUM_PATH} if _PW_CHROMIUM_PATH else {}))
        for w in WIDTHS:
            page = await browser.new_page(viewport={"width": w, "height": 900})
            await page.goto(FILE)
            await page.wait_for_timeout(500)
            overflow = await page.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
            print(f"width={w} guided: overflow={overflow}px")
            # Switch to Classic and recheck -- use the mobile hamburger below 600px,
            # the per-menu trigger above it (matches which one is actually visible).
            if w <= 600:
                await page.click("#mobileMenuTrigger")
                await page.wait_for_timeout(200)
                await page.click("#menuViewClassic")
            else:
                await page.click("#appMenuBar .menu-root:has-text('View') > button")
                await page.wait_for_timeout(150)
                await page.click("#menuViewClassic")
            await page.wait_for_timeout(300)
            overflow2 = await page.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
            print(f"width={w} classic: overflow={overflow2}px")
            await page.close()
        await browser.close()

asyncio.run(main())
