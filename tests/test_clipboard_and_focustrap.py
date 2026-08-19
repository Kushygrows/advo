import asyncio, sys
import os, pathlib

_PW_CHROMIUM_PATH = os.environ.get("PW_CHROMIUM_PATH")  # optional override; unset -> Playwright uses its own installed browser
from playwright.async_api import async_playwright

FILE = pathlib.Path(__file__).resolve().parent.parent.joinpath("advo.html").as_uri()

async def main():
    errors = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(**({"executable_path": _PW_CHROMIUM_PATH} if _PW_CHROMIUM_PATH else {}))
        context = await browser.new_context(permissions=["clipboard-read", "clipboard-write"])
        page = await context.new_page()
        page.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
        _IGNORED_CONSOLE_ERRORS = ("Failed to load resource: net::ERR_CONNECTION_REFUSED",)  # app's own best-effort local-AI-server probe (detectLocalAI()); expected/harmless with no local AI server running
        page.on("console", lambda m: errors.append(f"console.error: {m.text}") if m.type == "error" and m.text not in _IGNORED_CONSOLE_ERRORS else None)

        await page.goto(FILE)
        await page.wait_for_timeout(400)
        await page.click("#loadSampleFromSyncBtn")
        await page.wait_for_timeout(300)

        # ---- FIX 1a: normal clipboard path still works and still toasts ----
        await page.evaluate("guidedGoTo(4)")
        await page.wait_for_timeout(200)
        await page.evaluate("document.querySelectorAll('.toast').forEach(t=>t.remove())")
        await page.click(".copyBtn")
        await page.wait_for_timeout(300)
        toast_text = await page.locator(".toast").first.inner_text()
        print("toast after normal copy:", toast_text)
        assert "Copied" in toast_text
        clip = await page.evaluate("navigator.clipboard.readText()")
        print("clipboard contents after normal copy (truncated):", clip[:60])
        assert len(clip) > 0
        print("Test1 PASSED: normal Clipboard API path still copies and toasts")

        # ---- FIX 1b: simulate a rejected/broken Clipboard API -> must still
        # succeed via the legacy fallback and still show a toast, not fail silently ----
        await page.evaluate("""() => {
            Object.defineProperty(navigator, 'clipboard', {
                value: { writeText: () => Promise.reject(new Error('simulated permission denied')) },
                configurable: true
            });
        }""")
        await page.evaluate("document.querySelectorAll('.toast').forEach(t=>t.remove())")
        await page.click(".copyBtn")
        await page.wait_for_timeout(300)
        toasts_after_fallback = await page.locator(".toast").count()
        toast_text2 = await page.locator(".toast").first.inner_text() if toasts_after_fallback else ""
        print("toast count after broken Clipboard API:", toasts_after_fallback, "| text:", toast_text2)
        assert toasts_after_fallback > 0, "a broken Clipboard API must still produce user feedback, never silence"
        assert "Copied" in toast_text2, "legacy fallback should still fire the original success toast"
        print("Test2 PASSED: broken Clipboard API falls back to execCommand and still toasts")

        # ---- FIX 1c: simulate BOTH paths failing -> must show the plain-language warn toast, never silent ----
        await page.evaluate("""() => {
            Object.defineProperty(navigator, 'clipboard', {
                value: { writeText: () => Promise.reject(new Error('simulated failure')) },
                configurable: true
            });
            document.execCommand = () => { throw new Error('simulated execCommand failure'); };
        }""")
        await page.evaluate("document.querySelectorAll('.toast').forEach(t=>t.remove())")
        await page.click(".copyBtn")
        await page.wait_for_timeout(300)
        warn_toast = await page.locator(".toast.warn").count()
        print("warn toast count when both copy paths fail:", warn_toast)
        assert warn_toast > 0, "total copy failure must surface a plain warning, never do nothing"
        print("Test3 PASSED: total copy failure surfaces an explicit warning instead of silence")

        # reload to undo the clipboard/execCommand monkeypatches -- autosave
        # already restored the facts from the earlier load, so there's no
        # empty-state "see an example" button to click this time.
        await page.goto(FILE)
        await page.wait_for_timeout(400)

        # ---- FIX 2a: teleprompter focus trap ----
        await page.evaluate("openTeleprompter('Test script line one. Test script line two.')")
        await page.wait_for_timeout(200)
        tp_focusables = await page.evaluate("""() => {
            const overlay = document.getElementById('teleprompterOverlay');
            return Array.from(overlay.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'))
                .filter(el => !el.disabled && el.offsetParent !== null).length;
        }""")
        print("teleprompter focusable count:", tp_focusables)
        # Tab one more time than there are focusable elements; focus must still be inside the overlay.
        for _ in range(tp_focusables + 2):
            await page.keyboard.press("Tab")
        still_inside = await page.evaluate("""() => {
            const overlay = document.getElementById('teleprompterOverlay');
            return overlay.contains(document.activeElement);
        }""")
        print("focus still inside teleprompter after over-tabbing:", still_inside)
        assert still_inside, "Tab must cycle within the teleprompter overlay, never escape to the page behind it"
        await page.keyboard.press("Escape")
        await page.wait_for_timeout(200)
        tp_open = await page.evaluate("document.getElementById('teleprompterOverlay').classList.contains('open')")
        assert not tp_open
        print("Test4 PASSED: teleprompter traps Tab focus and Escape still closes it")

        # ---- FIX 2b: unlock overlay focus trap + Escape (previously had neither) ----
        # newSubjectInput lives on guided step 1 -- jump back there first so
        # it's actually visible/focusable (it was hidden at step 4).
        await page.evaluate("guidedGoTo(1)")
        await page.wait_for_timeout(150)
        await page.evaluate("document.getElementById('newSubjectInput').focus(); showUnlockOverlay();")
        await page.wait_for_timeout(200)
        active_on_open = await page.evaluate("document.activeElement.id")
        print("active element right after showUnlockOverlay():", active_on_open)
        assert active_on_open == "unlockPassInput"

        ul_focusables = await page.evaluate("""() => {
            const overlay = document.getElementById('unlockOverlay');
            return Array.from(overlay.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'))
                .filter(el => !el.disabled && el.offsetParent !== null).length;
        }""")
        print("unlock overlay focusable count:", ul_focusables)
        for _ in range(ul_focusables + 2):
            await page.keyboard.press("Tab")
        still_inside_unlock = await page.evaluate("""() => {
            const overlay = document.getElementById('unlockOverlay');
            return overlay.contains(document.activeElement);
        }""")
        print("focus still inside unlock overlay after over-tabbing:", still_inside_unlock)
        assert still_inside_unlock, "Tab must cycle within the unlock overlay too — this one had NO trap at all before the fix"

        await page.keyboard.press("Escape")
        await page.wait_for_timeout(200)
        ul_open = await page.evaluate("document.getElementById('unlockOverlay').classList.contains('open')")
        assert not ul_open, "Escape should dismiss the unlock overlay (mirrors the existing Continue-without-unlocking button)"
        focus_restored = await page.evaluate("document.activeElement.id")
        print("focus restored to after Escape-close:", focus_restored)
        assert focus_restored == "newSubjectInput", "focus should return to whatever was focused before the overlay opened"
        print("Test5 PASSED: unlock overlay now traps focus, supports Escape, and restores focus on close (none of this existed before)")

        if errors:
            print("ERRORS FOUND:")
            for e in errors: print(" -", e)
        else:
            print("No console/page errors.")

        await browser.close()
        if errors: sys.exit(1)
        print("ALL CLIPBOARD + FOCUS-TRAP TESTS PASSED")

asyncio.run(main())
