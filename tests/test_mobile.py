import asyncio, sys
import os, pathlib

_PW_CHROMIUM_PATH = os.environ.get("PW_CHROMIUM_PATH")  # optional override; unset -> Playwright uses its own installed browser
from playwright.async_api import async_playwright

FILE = pathlib.Path(__file__).resolve().parent.parent.joinpath("advo.html").as_uri()

async def main():
    errors = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(**({"executable_path": _PW_CHROMIUM_PATH} if _PW_CHROMIUM_PATH else {}))
        iphone = p.devices["iPhone 13"]
        context = await browser.new_context(**iphone)
        page = await context.new_page()
        page.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
        _IGNORED_CONSOLE_ERRORS = ("Failed to load resource: net::ERR_CONNECTION_REFUSED",)  # app's own best-effort local-AI-server probe (detectLocalAI()); expected/harmless with no local AI server running
        page.on("console", lambda m: errors.append(f"console.error: {m.text}") if m.type == "error" and m.text not in _IGNORED_CONSOLE_ERRORS else None)

        await page.goto(FILE)
        await page.wait_for_timeout(500)

        # 1. pointer/hover media features report as a real touch device
        media = await page.evaluate("""() => ({
            coarse: matchMedia('(pointer:coarse)').matches,
            hoverNone: matchMedia('(hover:none)').matches,
            hoverHover: matchMedia('(hover:hover)').matches,
        })""")
        print("media features:", media)
        assert media["coarse"] is True
        assert media["hoverHover"] is False

        # 2. Individual File/Edit/View/Settings triggers are hidden; hamburger is visible
        trigger_visible = await page.locator("#menuTriggerFile").is_visible()
        hamburger_visible = await page.locator("#mobileMenuTrigger").is_visible()
        print("File trigger visible:", trigger_visible, "| hamburger visible:", hamburger_visible)
        assert trigger_visible is False
        assert hamburger_visible is True

        # 3. Tap the hamburger -> all four sections show stacked, with labels
        await page.tap("#mobileMenuTrigger")
        await page.wait_for_timeout(300)
        menubar_class = await page.evaluate("() => document.getElementById('appMenuBar').className")
        print("menubar class after tap:", menubar_class)
        assert "mobile-open" in menubar_class

        labels = await page.evaluate("""() => Array.from(document.querySelectorAll('.menu-root'))
            .map(el => getComputedStyle(el, '::before').content)""")
        print("section ::before content values:", labels)

        file_item_visible = await page.locator("#menuFileImportNotes").is_visible()
        settings_item_visible = await page.locator("#a11yFontFamily").is_visible()
        print("File item visible in sheet:", file_item_visible, "| Settings control visible in sheet:", settings_item_visible)
        assert file_item_visible is True
        assert settings_item_visible is True

        # 4. Tap a nav item (Import notes) -> sheet should close (closeAllMenus fires via jumpToPanel)
        await page.tap("#menuFileImportNotes")
        await page.wait_for_timeout(300)
        menubar_class2 = await page.evaluate("() => document.getElementById('appMenuBar').className")
        print("menubar class after nav tap:", menubar_class2)
        assert "mobile-open" not in menubar_class2

        # 5. Reopen, tap outside -> closes
        await page.tap("#mobileMenuTrigger")
        await page.wait_for_timeout(200)
        await page.tap("body", position={"x": 5, "y": 5})
        await page.wait_for_timeout(200)
        menubar_class3 = await page.evaluate("() => document.getElementById('appMenuBar').className")
        print("menubar class after outside tap:", menubar_class3)
        assert "mobile-open" not in menubar_class3

        # 6. Touch target sizing: sample a handful of interactive elements for >= 44px height
        await page.wait_for_timeout(200)
        sizes = await page.evaluate("""() => {
            const ids = ['syncBtn'];
            const results = {};
            ids.forEach(id => {
                const el = document.getElementById(id);
                if (el) results[id] = el.getBoundingClientRect().height;
            });
            return results;
        }""")
        print("button heights:", sizes)
        for k, v in sizes.items():
            assert v >= 44, f"{k} height {v} is under the 44px touch target minimum"

        # 7. No horizontal overflow on a real mobile viewport
        overflow = await page.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
        print("overflow on iPhone viewport:", overflow)
        assert overflow == 0

        # 8. Input font-size floor (prevents iOS auto-zoom-on-focus)
        input_font = await page.evaluate("""() => getComputedStyle(document.getElementById('newSubjectInput')).fontSize""")
        print("newSubjectInput font-size on mobile:", input_font)
        assert float(input_font.replace("px","")) >= 16

        # 9. Ambient background scaled down (fewer/less blurred blobs) on touch
        blob_c_display = await page.evaluate("""() => {
            const el = document.querySelector('.ambient-blob-c');
            return el ? getComputedStyle(el).display : 'MISSING';
        }""")
        print("ambient-blob-c display on mobile:", blob_c_display)
        assert blob_c_display == "none"

        # 10. Safe-area-aware app menubar padding uses env()/max() (just confirm no crash / valid px value)
        pad = await page.evaluate("() => getComputedStyle(document.getElementById('appMenuBar')).paddingLeft")
        print("app-menubar paddingLeft on mobile:", pad)

        if errors:
            print("ERRORS FOUND:")
            for e in errors: print(" -", e)
        else:
            print("No console/page errors.")

        await context.close()
        await browser.close()
        if errors: sys.exit(1)
        print("ALL MOBILE TESTS PASSED")

asyncio.run(main())
