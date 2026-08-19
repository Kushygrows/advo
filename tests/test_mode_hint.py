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

        # 1. On fresh load (auto-restored mode), hint should be empty/not shown
        hint_initial = await page.evaluate("() => document.getElementById('modeSwitchHint').textContent")
        hint_initial_class = await page.evaluate("() => document.getElementById('modeSwitchHint').className")
        print("Initial hint text:", repr(hint_initial), "class:", hint_initial_class)
        assert hint_initial == "" and "show" not in hint_initial_class

        # 2. Click Classic tab -> hint should appear with Classic text
        await page.click("#modeClassicBtn")
        await page.wait_for_timeout(400)
        hint_text = await page.evaluate("() => document.getElementById('modeSwitchHint').textContent")
        hint_class = await page.evaluate("() => document.getElementById('modeSwitchHint').className")
        opacity = await page.evaluate("() => getComputedStyle(document.getElementById('modeSwitchHint')).opacity")
        print("After Classic click - text:", hint_text, "class:", hint_class, "opacity:", opacity)
        assert "Classic" in hint_text
        assert "show" in hint_class
        assert float(opacity) > 0.5

        # 3. Wait for it to fade back out (timer is 2600ms, then CSS fade .9s -> check well after)
        await page.wait_for_timeout(3200)
        hint_class_after = await page.evaluate("() => document.getElementById('modeSwitchHint').className")
        opacity_after = await page.evaluate("() => getComputedStyle(document.getElementById('modeSwitchHint')).opacity")
        print("After waiting - class:", hint_class_after, "opacity:", opacity_after)
        assert "show" not in hint_class_after
        assert float(opacity_after) < 0.05

        # 4. Click Guided tab -> hint reappears with Guided text
        await page.click("#modeGuidedBtn")
        await page.wait_for_timeout(400)
        hint_text2 = await page.evaluate("() => document.getElementById('modeSwitchHint').textContent")
        opacity2 = await page.evaluate("() => getComputedStyle(document.getElementById('modeSwitchHint')).opacity")
        print("After Guided click - text:", hint_text2, "opacity:", opacity2)
        assert "Guided" in hint_text2
        assert float(opacity2) > 0.5

        # 5. Reload -- confirm the auto-restored mode does NOT show a hint (persisted pref = guided)
        await page.reload()
        await page.wait_for_timeout(500)
        hint_after_reload = await page.evaluate("() => document.getElementById('modeSwitchHint').textContent")
        class_after_reload = await page.evaluate("() => document.getElementById('modeSwitchHint').className")
        print("After reload - text:", repr(hint_after_reload), "class:", class_after_reload)
        assert hint_after_reload == "" and "show" not in class_after_reload

        # 6. Menu-driven selection (View > Classic) should also trigger the hint
        await page.click("#appMenuBar .menu-root:has-text('View') > button")
        await page.wait_for_timeout(200)
        await page.click("#menuViewClassic")
        await page.wait_for_timeout(400)
        hint_text3 = await page.evaluate("() => document.getElementById('modeSwitchHint').textContent")
        print("After menu Classic click - text:", hint_text3)
        assert "Classic" in hint_text3

        # 7. jumpToPanel's automatic classic-switch should NOT trigger the mode hint text change to stay silent
        # Switch back to guided first
        await page.click("#modeGuidedBtn")
        await page.wait_for_timeout(3200)  # let it fade fully first
        # jump to a classic-only panel (e.g. video outline) which auto-switches to classic
        await page.click("#appMenuBar .menu-root:has-text('View') > button")
        await page.wait_for_timeout(150)
        await page.click("#menuViewVideoOutline")
        await page.wait_for_timeout(150)
        hint_class_after_jump = await page.evaluate("() => document.getElementById('modeSwitchHint').className")
        print("After jumpToPanel auto-switch - class:", hint_class_after_jump)
        assert "show" not in hint_class_after_jump, "jumpToPanel's silent classic-switch should not trigger the hint"

        if errors:
            print("ERRORS:")
            for e in errors: print(" -", e)
        else:
            print("No console/page errors.")
        await browser.close()
        if errors: sys.exit(1)
        print("ALL MODE HINT TESTS PASSED")

asyncio.run(main())
