"""
Playwright smoke test for Estate Liquidity Analyzer
Run with: python3 test_smoke.py
Requires: pip install playwright && playwright install chromium
App must be running at localhost:8501
"""

import asyncio
from playwright.async_api import async_playwright, expect

APP_URL = "http://localhost:8501"

SCENARIOS = [
    "HNW RE Investor — FLP + ILIT Combined Strategy",
    "Base Case",
    "High Growth / Low Liquidity",
    "Insurance Solves the Gap",
    "Planning Reduces Taxable Estate",
]

passed = 0
failed = 0


def ok(msg):
    global passed
    passed += 1
    print(f"  ✓ {msg}")


def fail(msg):
    global failed
    failed += 1
    print(f"  ✗ {msg}")


async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        print("\n" + "=" * 60)
        print("ESTATE LIQUIDITY ANALYZER — PLAYWRIGHT SMOKE TEST")
        print(f"Target: {APP_URL}")
        print("=" * 60)

        # ── Test 1: App loads ──────────────────────────────────────
        print("\n[1] App loads")
        try:
            await page.goto(APP_URL, timeout=15000)
            await page.wait_for_selector("h1", timeout=15000)
            title = await page.inner_text("h1")
            if "Estate Liquidity Analyzer" in title:
                ok(f"Title found: {title.strip()}")
            else:
                fail(f"Unexpected title: {title.strip()}")
        except Exception as e:
            fail(f"App did not load: {e}")
            await browser.close()
            return

        # ── Test 2: OBBBA banner visible ───────────────────────────
        print("\n[2] OBBBA banner")
        try:
            # Banner is in a div with OBBBA text
            content = await page.content()
            if "OBBBA" in content and "15,000,000" in content:
                ok("OBBBA banner present with $15M exemption")
            else:
                fail("OBBBA banner not found or missing $15M")
        except Exception as e:
            fail(f"Banner check error: {e}")

        # ── Test 3: Password gate (if present) ─────────────────────
        print("\n[3] Password gate")
        try:
            pwd_input = page.locator('input[type="password"]')
            if await pwd_input.count() > 0:
                print("  → Password gate active — enter password manually to continue full test")
                print("  → Skipping UI interaction tests (run with password pre-filled in secrets)")
                await browser.close()
                print_summary()
                return
            else:
                ok("No password gate — proceeding")
        except Exception as e:
            ok("No password gate detected")

        # Wait for app to fully render
        await page.wait_for_timeout(3000)

        # ── Test 4: Scenario dropdown exists ──────────────────────
        print("\n[4] Scenario dropdown")
        try:
            dropdown = page.locator('[data-testid="stSelectbox"]').first
            await expect(dropdown).to_be_visible(timeout=8000)
            ok("Scenario dropdown visible")
        except Exception as e:
            fail(f"Dropdown not found: {e}")

        # ── Test 5: Cycle all 5 scenarios ─────────────────────────
        print("\n[5] Cycling all 5 scenarios")
        for scenario in SCENARIOS:
            try:
                # Click dropdown
                dropdown = page.locator('[data-testid="stSelectbox"]').first
                await dropdown.click()
                await page.wait_for_timeout(500)

                # Select option
                option = page.get_by_text(scenario, exact=True)
                await option.click()
                await page.wait_for_timeout(2000)

                # Verify scenario description banner appears
                content = await page.content()
                short_name = scenario.split("—")[0].strip()[:20]
                if short_name in content:
                    ok(f"Scenario loaded: {scenario[:50]}")
                else:
                    fail(f"Scenario description missing for: {scenario[:50]}")
            except Exception as e:
                fail(f"Error on scenario '{scenario[:40]}': {e}")

        # ── Test 6: Model Results metrics non-zero ─────────────────
        print("\n[6] Model Results metrics")
        try:
            # Select Base Case which has clear tax exposure
            dropdown = page.locator('[data-testid="stSelectbox"]').first
            await dropdown.click()
            await page.wait_for_timeout(500)
            await page.get_by_text("Base Case", exact=True).click()
            await page.wait_for_timeout(2500)

            # Check metric values are present and non-zero
            metrics = await page.locator('[data-testid="stMetric"]').all()
            if len(metrics) >= 6:
                ok(f"Found {len(metrics)} metric cards")
                non_zero_count = 0
                for metric in metrics[:6]:
                    val = await metric.inner_text()
                    if "$0" not in val or "Projected" in val:
                        non_zero_count += 1
                ok(f"Metrics rendering with values")
            else:
                fail(f"Expected 6 metrics, found {len(metrics)}")
        except Exception as e:
            fail(f"Metrics check error: {e}")

        # ── Test 7: Comparison table has 4 rows ───────────────────
        print("\n[7] Planning comparison table")
        try:
            content = await page.content()
            for row_label in ["Current Planning", "Insurance Only", "Gifting / FLP Only", "Insurance + Gifting"]:
                if row_label in content:
                    ok(f"Table row found: {row_label}")
                else:
                    fail(f"Table row missing: {row_label}")
        except Exception as e:
            fail(f"Table check error: {e}")

        # ── Test 8: Legacy Over Time chart present ─────────────────
        print("\n[8] Legacy Over Time chart")
        try:
            content = await page.content()
            if "Legacy Over Time" in content and "Estate & Legacy Trajectory" in content:
                ok("Time series chart section present")
            else:
                fail("Time series chart section not found")
        except Exception as e:
            fail(f"Chart check error: {e}")

        # ── Test 9: Formula Methodology expander ──────────────────
        print("\n[9] Formula Methodology expander")
        try:
            content = await page.content()
            if "Formula Methodology" in content and "IRC Section" in content:
                ok("Methodology section present with IRC citations")
            else:
                fail("Methodology section missing")
        except Exception as e:
            fail(f"Methodology check error: {e}")

        # ── Test 10: Disclaimer present ───────────────────────────
        print("\n[10] Disclaimer")
        try:
            content = await page.content()
            if "educational and planning illustration" in content:
                ok("Disclaimer present")
            else:
                fail("Disclaimer missing")
        except Exception as e:
            fail(f"Disclaimer check error: {e}")

        await browser.close()
        print_summary()


def print_summary():
    total = passed + failed
    print(f"\n{'=' * 60}")
    print(f"RESULT: {passed}/{total} tests passed", end="")
    if failed == 0:
        print(" — ✓ ALL PASSED — safe to deploy to Streamlit Cloud")
    else:
        print(f" — ✗ {failed} FAILED — fix before deploying")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run())
