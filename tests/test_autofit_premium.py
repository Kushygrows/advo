import asyncio, sys
import os, pathlib

_PW_CHROMIUM_PATH = os.environ.get("PW_CHROMIUM_PATH")  # optional override; unset -> Playwright uses its own installed browser
from playwright.async_api import async_playwright

FILE = pathlib.Path(__file__).resolve().parent.parent.joinpath("advo.html").as_uri()

async def main():
    errors = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(**({"executable_path": _PW_CHROMIUM_PATH} if _PW_CHROMIUM_PATH else {}))
        page = await browser.new_page(viewport={"width":1280,"height":1100})
        page.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
        _IGNORED_CONSOLE_ERRORS = ("Failed to load resource: net::ERR_CONNECTION_REFUSED",)  # app's own best-effort local-AI-server probe (detectLocalAI()); expected/harmless with no local AI server running
        page.on("console", lambda m: errors.append(f"console.error: {m.text}") if m.type == "error" and m.text not in _IGNORED_CONSOLE_ERRORS else None)

        await page.goto(FILE)
        await page.wait_for_timeout(400)
        await page.click("#loadSampleFromSyncBtn")
        await page.wait_for_timeout(300)
        await page.evaluate("guidedGoTo(4)")
        await page.wait_for_timeout(200)

        # Force a long fact so the X draft is guaranteed to be over 280.
        await page.evaluate("""() => {
            facts.push({id:'FLONG', text:'A'.repeat(50) + '. ' + 'B'.repeat(60) + '. ' + 'C'.repeat(80) + '. ' + 'D'.repeat(100) + '. ' + 'E'.repeat(60) + '.', source:'https://example.gov/very-long-verified-source-page-about-this-topic-here'});
            state.factIndex = facts.length - 1;
            state.selectedPlatforms = new Set(['x']);
            renderFactBank(); renderToday(); renderPreviews();
        }""")
        await page.wait_for_timeout(300)

        count_text = await page.locator(".preview .count").first.inner_text()
        print("count badge (free X, long fact):", count_text)
        assert "auto-trimmed from" in count_text, "expected an auto-trim note on an over-limit free-tier X draft"

        format_note = await page.locator(".preview .notes").first.inner_text()
        print("format note:", format_note[:150])
        assert "OVER LIMIT" not in format_note, "should not show the old OVER LIMIT warning once auto-trimmed"
        assert "Automatically trimmed" in format_note

        preview_text = await page.locator(".preview .preview-text").first.inner_text()
        print("preview text length:", len(preview_text))
        assert "Source: https://example.gov" in preview_text, "source line must survive trimming, never get cut"
        assert preview_text.strip().split("Source:")[0].rstrip().endswith("…") or len(preview_text) < 500

        # Copy button payload should match what's shown (fitted, not the full original).
        copy_data = await page.locator(".copyBtn").first.get_attribute("data-text")
        import urllib.parse
        decoded = urllib.parse.unquote(copy_data)
        assert decoded == preview_text.replace(" "," ") or "…" in decoded
        print("Test1 PASSED: over-limit free-tier X draft auto-trims, keeps source intact, no OVER LIMIT warning")

        # Premium toggle should exist for X.
        premium_checkbox = page.locator(".premium-toggle-input")
        assert await premium_checkbox.count() == 1
        premium_label_text = await page.locator(".premium-toggle-label").inner_text()
        print("premium label:", premium_label_text)
        assert "25,000" in premium_label_text

        # Toggle premium on -> should now fit without trimming (since the
        # test fact is nowhere near 25,000 chars).
        await premium_checkbox.check()
        await page.wait_for_timeout(300)
        count_text2 = await page.locator(".preview .count").first.inner_text()
        print("count badge (premium X):", count_text2)
        assert "auto-trimmed" not in count_text2
        assert "/ 25000 chars" in count_text2
        preview_text2 = await page.locator(".preview .preview-text").first.inner_text()
        assert "A"*50 in preview_text2, "full untrimmed body should show once Premium unlocks enough room"
        print("Test2 PASSED: X Premium toggle raises the limit and un-trims the draft")

        # Non-premium platform (Threads) should show no premium toggle at all.
        await page.evaluate("state.selectedPlatforms = new Set(['threads']); renderPreviews();")
        await page.wait_for_timeout(300)
        threads_premium_count = await page.locator(".premium-toggle-input").count()
        print("premium toggle count for Threads:", threads_premium_count)
        assert threads_premium_count == 0, "Threads has no real premium tier — must not fabricate one"
        print("Test3 PASSED: no premium toggle shown for a platform without a real premium tier")

        # A normal, short draft under the limit should behave exactly as before.
        # (Reset the Premium toggle from Test2 so this actually exercises the
        # free-tier 280 limit, not the still-checked 25,000 one.)
        await page.evaluate("""() => {
            state.premiumPlatforms.delete('x');
            state.factIndex = 0;
            state.selectedPlatforms = new Set(['x']);
            renderToday(); renderPreviews();
        }""")
        await page.wait_for_timeout(300)
        count_text3 = await page.locator(".preview .count").first.inner_text()
        print("count badge (short draft, free X, premium reset off):", count_text3)
        assert "/ 280 chars" in count_text3, "expected free-tier 280 limit once Premium toggle is reset off"
        assert "auto-trimmed" not in count_text3
        checkbox_checked = await page.locator(".premium-toggle-input").is_checked()
        print("premium checkbox reflects reset state (should be False):", checkbox_checked)
        assert checkbox_checked is False, "checkbox UI must reflect state.premiumPlatforms after re-render"
        print("Test4 PASSED: short drafts under the free-tier limit are unaffected (no regression)")

        if errors:
            print("ERRORS FOUND:")
            for e in errors: print(" -", e)
        else:
            print("No console/page errors.")

        await browser.close()
        if errors: sys.exit(1)
        print("ALL AUTO-FIT + PREMIUM TESTS PASSED")

asyncio.run(main())
