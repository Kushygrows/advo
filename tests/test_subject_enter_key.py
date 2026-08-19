import asyncio, sys
import os, pathlib

_PW_CHROMIUM_PATH = os.environ.get("PW_CHROMIUM_PATH")  # optional override; unset -> Playwright uses its own installed browser
from playwright.async_api import async_playwright

FILE = pathlib.Path(__file__).resolve().parent.parent.joinpath("advo.html").as_uri()

async def main():
    errors = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(**({"executable_path": _PW_CHROMIUM_PATH} if _PW_CHROMIUM_PATH else {}))
        page = await browser.new_page(viewport={"width":1280,"height":900})
        page.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
        _IGNORED_CONSOLE_ERRORS = ("Failed to load resource: net::ERR_CONNECTION_REFUSED",)  # app's own best-effort local-AI-server probe (detectLocalAI()); expected/harmless with no local AI server running
        page.on("console", lambda m: errors.append(f"console.error: {m.text}") if m.type == "error" and m.text not in _IGNORED_CONSOLE_ERRORS else None)

        await page.goto(FILE)
        await page.wait_for_timeout(400)

        # Empty field: Enter should do nothing (no accidental sync on empty).
        await page.click("#newSubjectInput")
        await page.keyboard.press("Enter")
        await page.wait_for_timeout(300)
        prompt_row_visible_empty = await page.locator("#promptCopyRow").is_visible()
        print("prompt row visible after Enter on EMPTY field:", prompt_row_visible_empty)
        assert prompt_row_visible_empty is False, "Enter on an empty subject field should not trigger Sync"

        # Real subject + Enter should behave exactly like clicking Sync.
        await page.fill("#newSubjectInput", "Cannabis")
        await page.press("#newSubjectInput", "Enter")
        await page.wait_for_timeout(600)
        prompt_row_visible = await page.locator("#promptCopyRow").is_visible()
        paste_row_visible = await page.locator("#syncJsonImportRow").is_visible()
        print("prompt row visible after Enter:", prompt_row_visible, "| paste row visible:", paste_row_visible)
        assert prompt_row_visible and paste_row_visible, "Enter should trigger the same fallback flow as clicking Sync"

        # No page reload / navigation happened (would indicate a stray form submit).
        assert page.url.startswith("file://"), f"unexpected navigation: {page.url}"
        # Field value should still be there (page didn't reload/reset).
        val = await page.input_value("#newSubjectInput")
        assert val == "Cannabis"

        print("Test PASSED: Enter in subject field triggers Sync, empty field is a no-op, no navigation")

        if errors:
            print("ERRORS FOUND:")
            for e in errors: print(" -", e)
        else:
            print("No console/page errors.")

        await browser.close()
        if errors: sys.exit(1)
        print("ALL SUBJECT-ENTER TESTS PASSED")

asyncio.run(main())
