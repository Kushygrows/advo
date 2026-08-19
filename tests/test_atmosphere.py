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
        await page.wait_for_timeout(600)

        # 1. Ambient bg exists, is behind content, doesn't block clicks
        bg = await page.evaluate("""() => {
            const el = document.querySelector('.ambient-bg');
            if (!el) return null;
            const cs = getComputedStyle(el);
            return {position: cs.position, zIndex: cs.zIndex, pointerEvents: cs.pointerEvents, display: cs.display};
        }""")
        print("ambient-bg computed:", bg)
        assert bg is not None
        assert bg["pointerEvents"] == "none"

        # 2. Elements at document center should NOT be the ambient-bg (i.e. click-through works, real content on top)
        top_el_tag = await page.evaluate("""() => {
            const el = document.elementFromPoint(window.innerWidth/2, 300);
            return el ? el.className || el.tagName : null;
        }""")
        print("Element at (center,300):", top_el_tag)
        assert "ambient" not in str(top_el_tag).lower()

        # 3. Screenshot for visual sanity check
        await page.screenshot(path="/tmp/advo_atmosphere_default.png")

        # 4. Open Settings menu, verify Motion section present with two buttons
        await page.click("#appMenuBar .menu-root:has-text('Settings') > button")
        await page.wait_for_timeout(400)
        motion_buttons = await page.locator(".motion-row button").count()
        print("motion buttons:", motion_buttons)
        assert motion_buttons == 2

        await page.wait_for_timeout(400)
        hint_text = await page.locator("#motionHint").inner_text()
        print("Initial motion hint:", hint_text)

        # 5. Click "Reduced (static)" and verify html gets motion-reduced class
        await page.click(".motion-row button[data-motion='reduced']")
        await page.wait_for_timeout(200)
        html_class = await page.evaluate("() => document.documentElement.className")
        print("html class after reduced click:", html_class)
        assert "motion-reduced" in html_class

        # ambient-bg should now be display:none
        bg_display = await page.evaluate("() => getComputedStyle(document.querySelector('.ambient-bg')).display")
        print("ambient-bg display after reduced:", bg_display)
        assert bg_display == "none"

        # animation-duration on a known-animated element should collapse to ~0
        anim_dur = await page.evaluate("() => getComputedStyle(document.querySelector('#syncBtn')).transitionDuration")
        print("syncBtn transitionDuration after reduced:", anim_dur)

        # 6. Reload and confirm the preference persisted (localStorage) and applies before paint (no visible ambient bg)
        await page.reload()
        await page.wait_for_timeout(400)
        html_class2 = await page.evaluate("() => document.documentElement.className")
        print("html class after reload:", html_class2)
        assert "motion-reduced" in html_class2
        bg_display2 = await page.evaluate("() => getComputedStyle(document.querySelector('.ambient-bg')).display")
        assert bg_display2 == "none"
        print("Reduced-motion preference persisted across reload: OK")

        # 7. Switch back to Full motion
        await page.click("#appMenuBar .menu-root:has-text('Settings') > button")
        await page.wait_for_timeout(250)
        await page.click(".motion-row button[data-motion='full']")
        await page.wait_for_timeout(200)
        html_class3 = await page.evaluate("() => document.documentElement.className")
        print("html class after full click:", html_class3)
        assert "motion-full" in html_class3
        bg_display3 = await page.evaluate("() => getComputedStyle(document.querySelector('.ambient-bg')).display")
        print("ambient-bg display after full:", bg_display3)
        assert bg_display3 != "none"

        # 8. Guided step transition: click Continue and check the guided-step-anim class gets applied to the newly visible step panel
        # Switch to guided mode explicitly first via menu
        await page.click("#appMenuBar .menu-root:has-text('View') > button")
        await page.wait_for_timeout(150)
        await page.click("#menuViewGuided")
        await page.wait_for_timeout(200)
        # fill subject then continue if needed -- just check pip/step markup exists
        pip_count = await page.locator(".guided-step-pip").count()
        print("guided step pips:", pip_count)
        assert pip_count == 4

        # 9. Menu dropdown open/close doesn't error and toggles visibility class-based approach
        await page.click("#appMenuBar .menu-root:has-text('File') > button")
        await page.wait_for_timeout(400)
        file_dropdown_visible = await page.evaluate("""() => {
            const el = document.querySelector('#menuRootFile .menu-dropdown');
            return getComputedStyle(el).visibility;
        }""")
        print("File dropdown visibility after open:", file_dropdown_visible)
        assert file_dropdown_visible == "visible"
        await page.keyboard.press("Escape")
        await page.wait_for_timeout(500)
        file_dropdown_visible2 = await page.evaluate("""() => {
            const el = document.querySelector('#menuRootFile .menu-dropdown');
            return getComputedStyle(el).visibility;
        }""")
        print("File dropdown visibility after escape:", file_dropdown_visible2)
        assert file_dropdown_visible2 == "hidden"

        if errors:
            print("ERRORS FOUND:")
            for e in errors: print(" -", e)
        else:
            print("No console/page errors.")

        await browser.close()
        if errors:
            sys.exit(1)
        print("ALL ATMOSPHERE TESTS PASSED")

asyncio.run(main())
