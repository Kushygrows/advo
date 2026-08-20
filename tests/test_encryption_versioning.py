import asyncio
import os, pathlib

_PW_CHROMIUM_PATH = os.environ.get("PW_CHROMIUM_PATH")  # optional override; unset -> Playwright uses its own installed browser
from playwright.async_api import async_playwright

FILE = pathlib.Path(__file__).resolve().parent.parent.joinpath("advo.html").as_uri()

# Covers the 2026-08-20 security fix: PBKDF2 iteration count is now
# versioned (payload.v) instead of a single constant, specifically so
# raising it later never breaks decrypting blobs written under an older,
# lower count. This has zero prior test coverage (encryption wasn't
# covered by any existing regression test), and the change touches the
# actual crypto call sites -- worth a real test, not just a read-through.

async def main():
    errors = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(**({"executable_path": _PW_CHROMIUM_PATH} if _PW_CHROMIUM_PATH else {}))
        page = await browser.new_page()
        page.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
        page.on("console", lambda m: errors.append(f"console.error: {m.text}") if m.type == "error" else None)

        await page.goto(FILE)
        await page.wait_for_timeout(300)

        # ---- new encryption round-trips and is stamped with the current version ----
        result = await page.evaluate("""async () => {
            const payload = await encryptJSON("test-passphrase-123", {hello: "world", n: 42});
            const decrypted = await decryptJSON("test-passphrase-123", payload);
            return { v: payload.v, decrypted };
        }""")
        print("new encryption version:", result["v"])
        print("round-tripped value:", result["decrypted"])
        assert result["v"] == 2, f"expected current version 2, got {result['v']}"
        assert result["decrypted"] == {"hello": "world", "n": 42}
        print("Test1 PASSED: new encryption round-trips and is stamped v2")

        # ---- a blob encrypted under the OLD v1 iteration count must still decrypt ----
        # Simulates what a real pre-fix blob looks like: built by hand using
        # v1's iteration count (250000) directly, bypassing encryptJSON
        # (which now always writes v2) so this actually exercises the
        # backward-compat fallback path in decryptJSON, not just today's
        # write path.
        old_blob_result = await page.evaluate("""async () => {
            const salt = crypto.getRandomValues(new Uint8Array(16));
            const iv = crypto.getRandomValues(new Uint8Array(12));
            const key = await deriveAesKey("old-passphrase-456", salt, PBKDF2_ITERATIONS_BY_VERSION[1]);
            const enc = new TextEncoder();
            const ciphertext = await crypto.subtle.encrypt({name:"AES-GCM", iv}, key, enc.encode(JSON.stringify({legacy: true})));
            const oldStylePayload = { encrypted:true, v:1, salt:bufToBase64(salt), iv:bufToBase64(iv), data:bufToBase64(ciphertext) };
            const decrypted = await decryptJSON("old-passphrase-456", oldStylePayload);
            return decrypted;
        }""")
        print("old v1-style blob decrypted to:", old_blob_result)
        assert old_blob_result == {"legacy": True}
        print("Test2 PASSED: a v1-style blob (old iteration count) still decrypts correctly under the new version-gated code")

        # ---- wrong passphrase still fails loudly (unchanged behavior, sanity check) ----
        wrong_pass_threw = await page.evaluate("""async () => {
            const payload = await encryptJSON("right-pass", {a:1});
            try {
                await decryptJSON("wrong-pass", payload);
                return false;
            } catch (e) {
                return true;
            }
        }""")
        assert wrong_pass_threw, "a wrong passphrase must still throw, not silently return garbage"
        print("Test3 PASSED: wrong passphrase still throws (AES-GCM auth tag check unaffected by versioning change)")

        if errors:
            print("ERRORS FOUND:")
            for e in errors: print(" -", e)
        else:
            print("No console/page errors.")

        await browser.close()
        if errors: sys.exit(1)
        print("ALL ENCRYPTION VERSIONING TESTS PASSED")

import sys
asyncio.run(main())
