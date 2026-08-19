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
        await page.wait_for_timeout(400)

        # Load sample data so there's a real fact bank to work with.
        await page.click("#loadSampleFromSyncBtn")
        await page.wait_for_timeout(300)
        await page.evaluate("guidedGoTo(4)")
        await page.wait_for_timeout(300)

        # 1. Video outline builder should now be VISIBLE in Guided mode at step 4.
        video_panel_visible = await page.locator("#videoOutlinePanel").is_visible()
        print("video outline panel visible in Guided step 4:", video_panel_visible)
        assert video_panel_visible, "Video outline builder should be reachable from Guided mode step 4"

        # 2. School report chip should exist in the platform list.
        platform_list_text = await page.locator("#platformList").inner_text()
        print("platform list contains 'School report':", "School report" in platform_list_text)
        assert "School report" in platform_list_text

        # 3. Selecting ONLY the video outline (no platform) should satisfy step 4's validation.
        await page.evaluate("state.selectedPlatforms.clear(); renderPlatforms();")
        await page.click("#autoPickBtn")
        await page.wait_for_timeout(300)
        tip = await page.evaluate("validateGuidedStep(4)")
        print("validateGuidedStep(4) with video facts picked, no platform:", tip)
        assert tip is None, "Picking video facts alone should be enough to pass step 4 validation"

        # 4. Generate the video outline, confirm it produces real output.
        await page.click("#buildOutlineBtn")
        await page.wait_for_timeout(300)
        outline_text = await page.locator("#outlineOutput").inner_text()
        print("outline output length:", len(outline_text))
        assert len(outline_text) > 50
        print("Test1 PASSED: video outline reachable + usable from Guided mode, satisfies step validation alone")

        # 5. School report: select it as a platform/output type, confirm preview renders
        #    with a headline, sources list, and the "put into your own words" note.
        await page.evaluate("state.selectedPlatforms = new Set(['report']); renderPlatforms();")
        await page.wait_for_timeout(300)
        preview_text = await page.locator("#previewContainer").inner_text()
        print("preview contains 'A Report':", "A Report" in preview_text)
        print("preview contains 'Sources:':", "Sources:" in preview_text)
        assert "A Report" in preview_text
        assert "Sources:" in preview_text
        assert "own words" in preview_text.lower()
        print("Test2 PASSED: School report output type generates a sourced report draft")

        # 6. jumpToPanel to the video outline from the menu should land on
        #    Guided step 4, not force a switch to Classic (regression check
        #    on the guided-hide -> data-guided-step change).
        await page.evaluate("guidedGoTo(1)")
        await page.wait_for_timeout(200)
        await page.evaluate("jumpToPanel('videoOutlinePanel')")
        await page.wait_for_timeout(300)
        mode_after = await page.evaluate("uiMode")
        step_after = await page.evaluate("guidedStep")
        print("mode after jumpToPanel to video outline:", mode_after, "| step:", step_after)
        assert mode_after == "guided"
        assert step_after == 4
        print("Test3 PASSED: jumping to the video outline panel stays in Guided mode at step 4")

        if errors:
            print("ERRORS FOUND:")
            for e in errors: print(" -", e)
        else:
            print("No console/page errors.")

        await browser.close()
        if errors: sys.exit(1)
        print("ALL VIDEO+REPORT TESTS PASSED")

asyncio.run(main())
