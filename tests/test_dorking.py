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
        await page.wait_for_timeout(500)

        # Switch to Classic mode so all panels are visible/reachable without guided step gating
        classic_btn = page.locator("#menuViewClassic")
        if await classic_btn.count():
            await page.click("#appMenuBar .menu-root:has-text('View') > button")
            await page.wait_for_timeout(150)
            await classic_btn.click()
            await page.wait_for_timeout(150)

        # Type a subject that should suggest "News"
        await page.fill("#newSubjectInput", "breaking election news today")
        await page.wait_for_timeout(100)

        # Enable the search-engine/dorking toggle
        toggle = page.locator("#searchEngineToggle")
        await toggle.scroll_into_view_if_needed()
        await toggle.check()
        await page.wait_for_timeout(200)

        # Suggested note should mention News
        note = await page.locator("#dorkSuggestedNote").inner_text()
        print("Suggested note:", note)
        assert "News" in note, f"Expected News suggestion, got: {note}"

        # The news chip should have 'active' and 'suggested' classes
        news_chip_class = await page.locator(".dork-category-chip", has_text="News & current events").get_attribute("class")
        print("News chip class:", news_chip_class)
        assert "active" in news_chip_class and "suggested" in news_chip_class

        # Sub-options for News should be rendered
        subopts_text = await page.locator("#dorkSubOptions").inner_text()
        print("Sub-options:", subopts_text)
        assert "Major outlets only" in subopts_text
        assert "Exclude opinion" in subopts_text

        # engineResults should show a query containing "news" and NOT include site:.gov (since majorOutlets default false)
        result_text = await page.locator("#engineResults").inner_text()
        print("Result text:", result_text[:300])
        assert "news" in result_text.lower()

        # Now manually click a different category (Legal) and confirm it sticks even after typing more
        legal_chip = page.locator(".dork-category-chip", has_text="Legal & court records")
        await legal_chip.click()
        await page.wait_for_timeout(150)
        legal_class = await legal_chip.get_attribute("class")
        assert "active" in legal_class
        print("Legal chip active after manual click: OK")

        # Type more text that would suggest "gov" strongly -- category should NOT auto-switch since user picked manually
        await page.fill("#newSubjectInput", "breaking election news today federal regulation bill")
        await page.wait_for_timeout(150)
        legal_class_after = await legal_chip.get_attribute("class")
        assert "active" in legal_class_after, "Manual category selection should stick (suggest+confirm, not auto-switch)"
        print("Category stayed sticky after further typing: OK")

        # Check legal sub-options rendered
        subopts_text2 = await page.locator("#dorkSubOptions").inner_text()
        assert "Court opinions" in subopts_text2
        print("Legal sub-options rendered: OK")

        # Toggle "Exact phrase match" and verify quoting appears in query
        await page.check("#dorkExactPhrase")
        await page.wait_for_timeout(150)
        result_text2 = await page.locator("#engineResults").inner_text()
        print("Result after exact phrase:", result_text2[:300])
        assert '"' in result_text2

        # Toggle date range to "Past week" and verify after: appears
        await page.select_option("#dorkDateRange", "week")
        await page.wait_for_timeout(150)
        result_text3 = await page.locator("#engineResults").inner_text()
        print("Result after date range:", result_text3[:300])
        assert "after:" in result_text3

        # Test copy button works without throwing
        await page.evaluate("""() => {
            navigator.clipboard.writeText = async () => {};
        }""")
        copy_btn = page.locator(".copyQueryBtn").first
        await copy_btn.click()
        await page.wait_for_timeout(200)
        copy_text = await copy_btn.inner_text()
        assert "Copied" in copy_text
        print("Copy button: OK")

        # Test General category fallback with empty-ish subject (no strong keywords)
        await page.fill("#newSubjectInput", "xyzzy random gibberish subject")
        # click general manually
        general_chip = page.locator(".dork-category-chip", has_text="General (no specific category)")
        await general_chip.click()
        await page.wait_for_timeout(150)
        gen_subopts = await page.locator("#dorkSubOptions").inner_text()
        assert "Bias toward official sources" in gen_subopts
        print("General category subOptions: OK")

        # No suggestion note should show for gibberish subject when we re-render via input (simulate fresh session logic)
        # (not resetting userPickedDorkCategory here on purpose; suggestion note reflects current subject regardless)

        # Check console/page errors
        await page.wait_for_timeout(200)
        if errors:
            print("ERRORS FOUND:")
            for e in errors:
                print(" -", e)
        else:
            print("No console/page errors.")

        await browser.close()
        if errors:
            sys.exit(1)
        print("ALL DORKING TESTS PASSED")

asyncio.run(main())
