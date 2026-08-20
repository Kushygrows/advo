"""
Runs Advo's full Playwright regression suite against advo.html and exits
non-zero if anything fails. Used both by CI (.github/workflows/build.yml)
and for local checks before pushing a fix.

Usage:
    python3 tests/run_regression.py
"""
import subprocess
import sys
import pathlib

TESTS_DIR = pathlib.Path(__file__).resolve().parent

# The official regression suite. Keep this list in sync with what actually
# lives in this folder -- if you add a new test_*.py file here, add its name
# below too, or it will silently never run in CI.
TESTS = [
    "test_dorking.py",
    "test_smart_search.py",
    "test_stale_sample.py",
    "test_atmosphere.py",
    "test_atmosphere_overflow.py",
    "test_mode_hint.py",
    "test_mobile.py",
    "test_sync_paste_and_bottom_nav.py",
    "test_subject_enter_key.py",
    "test_video_and_report.py",
    "test_autofit_premium.py",
    "test_clipboard_and_focustrap.py",
    "test_encryption_versioning.py",
]


def main():
    missing = [t for t in TESTS if not (TESTS_DIR / t).exists()]
    if missing:
        print("ERROR: listed test file(s) not found in tests/:")
        for m in missing:
            print(f"  - {m}")
        sys.exit(1)

    # Runs first, and separately from the Playwright suite below, because a
    # stale CSP hash makes the ENTIRE app fail to run under CSP enforcement
    # -- if this doesn't run first, all 12 tests below would fail with
    # confusing, unrelated-looking browser errors instead of one clear
    # message pointing at the actual cause.
    print("=== Running verify_csp_hashes.py ===", flush=True)
    csp_check = subprocess.run([sys.executable, str(TESTS_DIR / "verify_csp_hashes.py")])
    if csp_check.returncode != 0:
        print("--- FAILED: verify_csp_hashes.py ---", flush=True)
        print("\nStale CSP hash(es) in advo.html -- fix this before running the", flush=True)
        print("rest of the suite, or every test below will fail confusingly.", flush=True)
        sys.exit(1)
    print("--- PASSED: verify_csp_hashes.py ---", flush=True)

    # cloud-worker's LicenseGate concurrency-safety tests -- Node, not
    # Python/Playwright, since it's testing server-side Worker logic, not
    # advo.html. Kept in the same regression run so one command still
    # catches everything.
    print("\n=== Running cloud-worker/test_license_gate.mjs ===", flush=True)
    gate_test = subprocess.run(["node", str(TESTS_DIR.parent / "cloud-worker" / "test_license_gate.mjs")])
    if gate_test.returncode != 0:
        print("--- FAILED: cloud-worker/test_license_gate.mjs ---", flush=True)
        sys.exit(1)
    print("--- PASSED: cloud-worker/test_license_gate.mjs ---", flush=True)

    failures = []
    for name in TESTS:
        path = TESTS_DIR / name
        print(f"\n=== Running {name} ===", flush=True)
        result = subprocess.run([sys.executable, str(path)])
        if result.returncode != 0:
            failures.append(name)
            print(f"--- FAILED: {name} ---", flush=True)
        else:
            print(f"--- PASSED: {name} ---", flush=True)

    print("\n" + "=" * 60)
    if failures:
        print(f"{len(failures)} of {len(TESTS)} regression test(s) FAILED:")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)

    print(f"All {len(TESTS)} regression tests passed.")


if __name__ == "__main__":
    main()
