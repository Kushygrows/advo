import asyncio, json
import os, pathlib

_PW_CHROMIUM_PATH = os.environ.get("PW_CHROMIUM_PATH")  # optional override; unset -> Playwright uses its own installed browser
from playwright.async_api import async_playwright

FILE = pathlib.Path(__file__).resolve().parent.parent.joinpath("advo.html").as_uri()

async def run_scenario(browser, payload):
    page = await browser.new_page()
    script = f"window.localStorage.setItem('advo_session_v1', {json.dumps(json.dumps(payload))});"
    await page.add_init_script(script)
    await page.goto(FILE)
    await page.wait_for_timeout(500)
    subject_val = await page.locator("#subjectInput").input_value()
    remaining_raw = await page.evaluate("() => localStorage.getItem('advo_session_v1')")
    body_text = await page.locator("body").inner_text()
    await page.close()
    return subject_val, remaining_raw, body_text

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(**({"executable_path": _PW_CHROMIUM_PATH} if _PW_CHROMIUM_PATH else {}))

        # --- Test 1: stale cannabis sample data (isSampleData:true, unknown subject) should be purged ---
        stale_payload = {
            "subject": "Oregon Cannabis Regulation (Aug 2026 baseline)",
            "facts": [
                {"id":"F1","text":"OLCC is not currently accepting new producer, processor, wholesaler, or retailer license applications.","source":"https://www.oregon.gov/olcc"},
            ],
            "factBankLoadedAt": "2026-08-17T00:00:00.000Z",
            "isSampleData": True,
            "historyLog": [],
            "videoSelected": []
        }
        subject_val, remaining, body_text = await run_scenario(browser, stale_payload)
        print("Test1 subject:", subject_val)
        assert "cannabis" not in subject_val.lower()
        assert remaining is None or "cannabis" not in remaining.lower()
        assert "cannabis" not in body_text.lower()
        print("Test 1 PASSED: stale cannabis sample purged, not shown.")

        # --- Test 2: a real (non-sample) saved session should NOT be wiped ---
        real_payload = {
            "subject": "My own research notes",
            "facts": [
                {"id":"F1","text":"A real user fact.","source":"https://example.com/real"},
            ],
            "factBankLoadedAt": "2026-08-17T00:00:00.000Z",
            "isSampleData": False,
            "historyLog": [],
            "videoSelected": []
        }
        subject_val2, remaining2, _ = await run_scenario(browser, real_payload)
        print("Test2 subject:", subject_val2)
        assert subject_val2 == "My own research notes"
        assert remaining2 is not None and "My own research notes" in remaining2
        print("Test 2 PASSED: real user data preserved.")

        # --- Test 3: a CURRENT valid sample topic restored as sample should still work normally ---
        current_sample_payload = {
            "subject": "Sleep & Circadian Rhythm Basics",
            "facts": [
                {"id":"F1","text":"Test fact.","source":"https://www.cdc.gov/sleep/about/index.html"},
            ],
            "factBankLoadedAt": "2026-08-17T00:00:00.000Z",
            "isSampleData": True,
            "historyLog": [],
            "videoSelected": []
        }
        subject_val3, remaining3, _ = await run_scenario(browser, current_sample_payload)
        print("Test3 subject:", subject_val3)
        assert subject_val3 == "Sleep & Circadian Rhythm Basics"
        assert remaining3 is not None
        page = await browser.new_page()
        await page.add_init_script(f"window.localStorage.setItem('advo_session_v1', {json.dumps(json.dumps(current_sample_payload))});")
        await page.goto(FILE)
        await page.wait_for_timeout(500)
        notice_text = await page.locator("#sampleDataNotice").inner_text()
        assert "example data" in notice_text.lower()
        await page.close()
        print("Test 3 PASSED: current valid sample topic still restores + shows banner normally.")

        # --- Test 4: brand-new user, zero localStorage -> empty fact bank, no cannabis anywhere ---
        page = await browser.new_page()
        await page.goto(FILE)
        await page.wait_for_timeout(500)
        body_text4 = await page.locator("body").inner_text()
        assert "cannabis" not in body_text4.lower()
        subject_val4 = await page.locator("#subjectInput").input_value()
        print("Test4 fresh-user subject:", repr(subject_val4))
        await page.close()
        print("Test 4 PASSED: brand-new user sees no cannabis content anywhere.")

        await browser.close()
        print("ALL STALE-SAMPLE TESTS PASSED")

asyncio.run(main())
