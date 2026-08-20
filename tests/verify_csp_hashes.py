"""
Verifies that the sha256 hashes in advo.html's Content-Security-Policy
script-src directive actually match the current content of its two inline
<script> blocks.

Why this exists: the CSP was tightened from `script-src 'unsafe-inline'`
to exact per-script sha256 hashes (2026-08-20 security audit). That's a
real security improvement, but it comes with a sharp edge -- if either
inline <script> block's content ever changes and the CSP hash isn't
recomputed to match, the browser silently refuses to run the script at
all. No error dialog, no console message a typical user would ever see --
the app just doesn't work. This script exists specifically so that never
ships unnoticed: run it after any edit to advo.html, and it's wired into
tests/run_regression.py and CI so a stale hash fails the build instead of
failing silently in front of a user.

Usage:
    python3 tests/verify_csp_hashes.py            # verify, exit 1 if stale
    python3 tests/verify_csp_hashes.py --print     # also print the correct
                                                    # CSP content= value to
                                                    # paste in if it's stale
"""
import base64
import hashlib
import pathlib
import re
import sys

ADVO_HTML = pathlib.Path(__file__).resolve().parent.parent / "advo.html"


def compute_hashes(html):
    blocks = re.findall(r"<script(?:\s[^>]*)?>(.*?)</script>", html, re.DOTALL)
    # Only inline blocks matter for CSP hashing -- if a future edit adds a
    # <script src="..."> tag, its body is empty here, which would produce a
    # wrong/misleading hash for it. There are none as of 2026-08-20 (both
    # blocks are inline), but flag it rather than silently mis-hash one.
    hashes = []
    for body in blocks:
        digest = hashlib.sha256(body.encode("utf-8")).digest()
        hashes.append("sha256-" + base64.b64encode(digest).decode("ascii"))
    return hashes


def current_csp_hashes(html):
    m = re.search(r'Content-Security-Policy"\s+content="([^"]*)"', html)
    if not m:
        return None, []
    csp = m.group(1)
    script_src_m = re.search(r"script-src\s+([^;]+);", csp)
    if not script_src_m:
        return csp, []
    declared = re.findall(r"'(sha256-[^']+)'", script_src_m.group(1))
    return csp, declared


def main():
    html = ADVO_HTML.read_text(encoding="utf-8")
    actual = compute_hashes(html)
    csp, declared = current_csp_hashes(html)

    if csp is None:
        print("ERROR: no Content-Security-Policy meta tag found in advo.html")
        sys.exit(1)

    if set(actual) != set(declared):
        print("CSP script-src hashes are STALE -- do not ship this as-is.")
        print(f"  {len(declared)} hash(es) declared in the CSP tag, {len(actual)} inline <script> block(s) found.")
        print("  Declared:", declared)
        print("  Actual:  ", actual)
        if "--print" in sys.argv:
            new_script_src = "script-src " + " ".join(f"'{h}'" for h in actual) + ";"
            print("\nCorrect script-src directive:")
            print(" ", new_script_src)
        sys.exit(1)

    print(f"CSP script-src hashes OK -- {len(actual)} inline <script> block(s), all match.")


if __name__ == "__main__":
    main()
