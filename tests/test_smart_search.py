import asyncio, sys
import os, pathlib

_PW_CHROMIUM_PATH = os.environ.get("PW_CHROMIUM_PATH")  # optional override; unset -> Playwright uses its own installed browser
from playwright.async_api import async_playwright

FILE = pathlib.Path(__file__).resolve().parent.parent.joinpath("advo.html").as_uri()

async def main():
    errors = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(**({"executable_path": _PW_CHROMIUM_PATH} if _PW_CHROMIUM_PATH else {}))
        page = await browser.new_page(viewport={"width":1280,"height":1000})
        page.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
        _IGNORED_CONSOLE_ERRORS = ("Failed to load resource: net::ERR_CONNECTION_REFUSED",)  # app's own best-effort local-AI-server probe (detectLocalAI()); expected/harmless with no local AI server running
        page.on("console", lambda m: errors.append(f"console.error: {m.text}") if m.type == "error" and m.text not in _IGNORED_CONSOLE_ERRORS else None)

        await page.goto(FILE)
        await page.wait_for_timeout(500)

        # 0. "dorking" word must not appear anywhere in visible page text
        body_text = await page.locator("body").inner_text()
        assert "dorking" not in body_text.lower(), "the word 'dorking' is still visible in the UI"
        print("Test0 PASSED: no 'dorking' text anywhere on the page")

        classic_btn = page.locator("#menuViewClassic")
        await page.click("#appMenuBar .menu-root:has-text('View') > button")
        await page.wait_for_timeout(150)
        await classic_btn.click()
        await page.wait_for_timeout(150)

        toggle = page.locator("#searchEngineToggle")
        await toggle.scroll_into_view_if_needed()

        # 1. Comparison detection: "Tesla vs Rivian"
        await page.fill("#newSubjectInput", "Tesla vs Rivian")
        await toggle.check()
        await page.wait_for_timeout(200)
        signals_text = await page.locator("#smartSignalsList").inner_text()
        print("Signals for 'Tesla vs Rivian':", signals_text)
        assert "Compare" in signals_text
        result_text = await page.locator("#engineResults").inner_text()
        print("Query for comparison:", result_text[:200])
        assert '("Tesla" OR "Rivian")' in result_text
        print("Test1 PASSED: comparison detection rewrites subject as OR group")

        # 2. Entity detection: Title Case proper name -> exact phrase
        await page.fill("#newSubjectInput", "Federal Reserve Interest Rates")
        await page.wait_for_timeout(200)
        signals_text2 = await page.locator("#smartSignalsList").inner_text()
        print("Signals for 'Federal Reserve Interest Rates':", signals_text2)
        assert "exact name/title" in signals_text2
        result_text2 = await page.locator("#engineResults").inner_text()
        print("Query for entity:", result_text2[:200])
        assert '"Federal Reserve Interest Rates"' in result_text2
        print("Test2 PASSED: Title Case entity gets exact-phrase wrapped")

        # 3. Ranking/superlative detection
        await page.fill("#newSubjectInput", "best electric cars")
        await page.wait_for_timeout(200)
        signals_text3 = await page.locator("#smartSignalsList").inner_text()
        print("Signals for 'best electric cars':", signals_text3)
        assert "ranked/reviewed" in signals_text3
        result_text3 = await page.locator("#engineResults").inner_text()
        assert "intitle:best" in result_text3
        print("Test3 PASSED: ranking language adds intitle operators")

        # 4. How-to detection
        await page.fill("#newSubjectInput", "how to fix a leaky faucet")
        await page.wait_for_timeout(200)
        signals_text4 = await page.locator("#smartSignalsList").inner_text()
        print("Signals for how-to subject:", signals_text4)
        assert "how-to" in signals_text4.lower() or "explainer" in signals_text4.lower()
        result_text4 = await page.locator("#engineResults").inner_text()
        assert "inurl:faq" in result_text4
        print("Test4 PASSED: how-to phrasing adds guide/faq operators")

        # 5. Explicit year detection
        await page.fill("#newSubjectInput", "minimum wage changes 2024")
        await page.wait_for_timeout(200)
        signals_text5 = await page.locator("#smartSignalsList").inner_text()
        print("Signals for year subject:", signals_text5)
        assert "2024" in signals_text5
        result_text5 = await page.locator("#engineResults").inner_text()
        assert "after:2024-01-01" in result_text5
        print("Test5 PASSED: explicit year adds after: filter")

        # 6. No false positive: plain lowercase generic subject gets no signals
        await page.fill("#newSubjectInput", "sleep and circadian rhythm basics")
        await page.wait_for_timeout(200)
        panel_visible = await page.locator("#smartSignalsPanel").is_visible()
        print("Smart panel visible for generic subject:", panel_visible)
        assert panel_visible is False
        print("Test6 PASSED: no false-positive signals for a plain generic subject")

        # 7. Toggle a detected signal off -> query reverts to not include it
        await page.fill("#newSubjectInput", "best electric cars")
        await page.wait_for_timeout(200)
        checkbox = page.locator("#smartSignalsList label", has_text="ranked/reviewed").locator("input")
        await checkbox.uncheck()
        await page.wait_for_timeout(200)
        result_text7 = await page.locator("#engineResults").inner_text()
        print("Query after unchecking ranking signal:", result_text7[:200])
        assert "intitle:best" not in result_text7
        print("Test7 PASSED: unchecking a detected signal removes it from the query")

        # 8. Manual-operators info badge (not a checkbox toggle)
        await page.fill("#newSubjectInput", "climate policy site:epa.gov")
        await page.wait_for_timeout(200)
        signals_text8 = await page.locator("#smartSignalsList").inner_text()
        print("Signals when user typed their own site: operator:", signals_text8)
        assert "kept as typed" in signals_text8
        result_text8 = await page.locator("#engineResults").inner_text()
        assert "site:epa.gov" in result_text8
        print("Test8 PASSED: pre-existing manual operators are preserved and flagged")

        if errors:
            print("ERRORS FOUND:")
            for e in errors: print(" -", e)
        else:
            print("No console/page errors.")

        await browser.close()
        if errors: sys.exit(1)
        print("ALL SMART SEARCH TESTS PASSED")

asyncio.run(main())
