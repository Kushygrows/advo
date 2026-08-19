import asyncio, sys, json
import os, pathlib

_PW_CHROMIUM_PATH = os.environ.get("PW_CHROMIUM_PATH")  # optional override; unset -> Playwright uses its own installed browser
from playwright.async_api import async_playwright

FILE = pathlib.Path(__file__).resolve().parent.parent.joinpath("advo.html").as_uri()

CANNABIS_JSON = {"subject": "Cannabis", "facts": [
    {"id": "F1", "text": "Marijuana (cannabis) remains classified as a Schedule I controlled substance under the federal Controlled Substances Act.", "source": "https://www.dea.gov/marijuana-rescheduling-regulatory-actions"},
    {"id": "F2", "text": "On April 23, 2026, the Justice Department and DEA issued an order placing FDA-approved marijuana drug products into Schedule III.", "source": "https://www.justice.gov/opa/pr/justice-department-places-fda-approved-marijuana-products-and-products-containing-marijuana"},
    {"id": "F3", "text": "DEA scheduled a formal administrative hearing on reclassifying marijuana, set to begin June 29, 2026.", "source": "https://www.federalregister.gov/documents/2026/04/28/2026-08177/schedules-of-controlled-substances-rescheduling-of-marijuana"}
]}

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

        # Guided mode is default. Clear localStorage sample-data confusion by
        # just proceeding directly to Sync step (step 1 is already active).
        assert await page.locator("body").evaluate("el => el.classList.contains('mode-guided')")

        # Trigger the copy/paste fallback the same way a user with no local
        # AI / API key / cloud key configured would hit it: type a subject
        # and click Sync.
        await page.fill("#newSubjectInput", "Cannabis")
        await page.click("#syncBtn")
        await page.wait_for_timeout(600)

        # The paste-JSON row should now be visible (this is the core bug fix).
        paste_row_visible = await page.locator("#syncJsonImportRow").is_visible()
        print("paste row visible after Sync fallback:", paste_row_visible)
        assert paste_row_visible, "syncJsonImportRow should be visible in Guided mode after the fallback triggers"

        # Paste the exact JSON shape a tester got back from an AI chat.
        await page.fill("#syncJsonPasteInput", json.dumps(CANNABIS_JSON))
        await page.click("#importPastedJsonBtn")
        await page.wait_for_timeout(400)

        status_text = await page.locator("#syncJsonPasteStatus").inner_text()
        print("paste status:", status_text)
        assert "3 facts added" in status_text or "Loaded" in status_text

        # Should have auto-advanced to guided step 2 (Review sources).
        current_step = await page.evaluate("guidedStep")
        print("guided step after import:", current_step)
        assert current_step == 2

        fact_bank_text = await page.locator("#factBankList").inner_text()
        assert "F1" in fact_bank_text
        print("Test1 PASSED: pasted JSON reachable + working in Guided mode")

        # Test the fenced-code-block tolerance (a common AI-chat quirk).
        await page.evaluate("guidedGoTo(1)")
        await page.wait_for_timeout(200)
        fenced = "```json\n" + json.dumps(CANNABIS_JSON) + "\n```"
        await page.fill("#syncJsonPasteInput", fenced)
        await page.click("#importPastedJsonBtn")
        await page.wait_for_timeout(400)
        status_text2 = await page.locator("#syncJsonPasteStatus").inner_text()
        print("paste status (fenced):", status_text2)
        assert "Loaded" in status_text2
        print("Test2 PASSED: code-fence-wrapped JSON still imports")

        # Bottom Continue/Back buttons: present, mirror top state, and work.
        await page.evaluate("guidedGoTo(2)")
        await page.wait_for_timeout(200)
        bottom_continue_visible = await page.locator("#guidedContinueBtnBottom").is_visible()
        bottom_back_visible = await page.locator("#guidedBackBtnBottom").is_visible()
        print("bottom continue visible:", bottom_continue_visible, "| bottom back visible:", bottom_back_visible)
        assert bottom_continue_visible and bottom_back_visible

        await page.click("#guidedContinueBtnBottom")
        await page.wait_for_timeout(200)
        step_after_bottom_continue = await page.evaluate("guidedStep")
        print("step after clicking bottom continue:", step_after_bottom_continue)
        assert step_after_bottom_continue == 3
        print("Test3 PASSED: bottom Continue button present and functional")

        # Bottom tip: blocked continue should show a tip at the bottom too.
        # Use a fresh page with an empty fact bank so step 1's validation
        # reliably blocks (step 4 has a platform pre-selected by default,
        # so it wouldn't block here).
        page2 = await browser.new_page(viewport={"width":1280,"height":900})
        await page2.goto(FILE)
        await page2.wait_for_timeout(400)
        await page2.evaluate("clearFactBank(true)")
        await page2.wait_for_timeout(200)
        await page2.click("#guidedContinueBtnBottom")
        await page2.wait_for_timeout(200)
        bottom_tip_text = await page2.locator("#guidedTipBottom").inner_text()
        top_tip_text = await page2.locator("#guidedTip").inner_text()
        print("bottom tip text on blocked continue:", bottom_tip_text)
        print("top tip text on blocked continue:", top_tip_text)
        assert len(bottom_tip_text.strip()) > 0
        assert bottom_tip_text.strip() == top_tip_text.strip()
        await page2.close()
        print("Test4 PASSED: validation tip also shows at the bottom")

        # Classic-mode file-based Import JSON still works (regression check
        # on the refactor).
        await page.click("#modeClassicBtn")
        await page.wait_for_timeout(200)
        import os
        tmp_json = "/tmp/test_import_facts.json"
        with open(tmp_json, "w") as f:
            json.dump(CANNABIS_JSON, f)
        async with page.expect_file_chooser() as fc_info:
            await page.click("label:has-text('Import JSON')")
        file_chooser = await fc_info.value
        await file_chooser.set_files(tmp_json)
        await page.wait_for_timeout(400)
        fact_bank_text2 = await page.locator("#factBankList").inner_text()
        assert "F1" in fact_bank_text2
        print("Test5 PASSED: Classic-mode file-based Import JSON still works after refactor")

        if errors:
            print("ERRORS FOUND:")
            for e in errors: print(" -", e)
        else:
            print("No console/page errors.")

        await browser.close()
        if errors: sys.exit(1)
        print("ALL SYNC-PASTE + BOTTOM-NAV TESTS PASSED")

asyncio.run(main())
