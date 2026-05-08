"""
Edge case unit tests for Estate Liquidity Analyzer calculations
Run with: python3 test_edge_cases.py
No browser or running app required.
"""

from calculations import EstateInputs, run_estate_model, forced_sale_risk_label, build_time_series
from scenarios import get_scenarios

passed = 0
failed = 0


def ok(msg):
    global passed
    passed += 1
    print(f"  ✓ {msg}")


def fail(msg, detail=""):
    global failed
    failed += 1
    print(f"  ✗ {msg}" + (f" — {detail}" if detail else ""))


print("\n" + "=" * 60)
print("ESTATE LIQUIDITY ANALYZER — EDGE CASE UNIT TESTS")
print("=" * 60)

# ── Test 1: Zero estate ────────────────────────────────────────
print("\n[1] Zero estate")
e = EstateInputs(0, 0, 0, 0, 0, 0.05, 0.03, 10, 15_000_000, 0.40, 0.01, 0, 0.0, False)
r = run_estate_model(e, True, True)
if r.projected_net_estate == 0:
    ok("Projected net estate is zero")
else:
    fail("Expected zero estate", f"got {r.projected_net_estate}")
if r.legacy_to_heirs == 0:
    ok("Legacy to heirs is zero")
else:
    fail("Expected zero legacy", f"got {r.legacy_to_heirs}")
if r.estimated_estate_tax == 0:
    ok("Estate tax is zero")
else:
    fail("Expected zero tax on zero estate", f"got {r.estimated_estate_tax}")

# ── Test 2: Below exemption = no tax ──────────────────────────
print("\n[2] Estate below $15M exemption")
e = EstateInputs(1_000_000, 0, 500_000, 200_000, 500_000, 0.05, 0.03, 10, 15_000_000, 0.40, 0.01, 0, 0.0, False)
r = run_estate_model(e, False, False)
if r.estimated_estate_tax == 0:
    ok(f"No estate tax — projected estate ${r.projected_net_estate:,.0f} < $15M exemption")
else:
    fail("Should have zero tax below exemption", f"got ${r.estimated_estate_tax:,.0f}")

# ── Test 3: ILIT reduces taxable estate ───────────────────────
print("\n[3] ILIT vs personally owned insurance")
base = dict(current_real_estate_value=8_000_000, current_debt=0, other_assets=8_000_000,
            liquid_assets=100_000, life_insurance_death_benefit=2_000_000,
            real_estate_appreciation_rate=0.06, other_asset_growth_rate=0.04,
            years_until_death=10, estate_tax_exemption=15_000_000,
            estate_tax_rate=0.40, probate_cost_rate=0.01, gifting_reduction_percent=0)

e_personal = EstateInputs(**base, flp_valuation_discount=0.0, insurance_in_ilit=False)
e_ilit = EstateInputs(**base, flp_valuation_discount=0.0, insurance_in_ilit=True)
r_personal = run_estate_model(e_personal, True, False)
r_ilit = run_estate_model(e_ilit, True, False)

if r_ilit.taxable_estate < r_personal.taxable_estate:
    ok(f"ILIT taxable estate ${r_ilit.taxable_estate:,.0f} < personal ${r_personal.taxable_estate:,.0f}")
else:
    fail("ILIT should reduce taxable estate vs personal ownership")

# ── Test 4: FLP gifting math ───────────────────────────────────
print("\n[4] FLP valuation discount math")
e = EstateInputs(10_000_000, 0, 5_000_000, 100_000, 1_000_000, 0.06, 0.04, 10,
                 15_000_000, 0.40, 0.01, 0.80, 0.30, False)
r = run_estate_model(e, False, True)

# Gifting reduction should be: projected_estate * 80% * (1 - 30%)
expected_ratio = 0.80 * (1 - 0.30)  # = 56% of projected estate
actual_ratio = r.gifting_reduction_amount / r.projected_net_estate

if abs(actual_ratio - expected_ratio) < 0.001:
    ok(f"FLP math correct: {actual_ratio:.1%} of projected estate removed (expected {expected_ratio:.1%})")
else:
    fail(f"FLP math wrong: got {actual_ratio:.1%}, expected {expected_ratio:.1%}")

if r.gifting_reduction_amount < r.projected_net_estate:
    ok(f"Gifting reduction ${r.gifting_reduction_amount:,.0f} < projected estate ${r.projected_net_estate:,.0f}")
else:
    fail("Gifting reduction exceeded projected estate")

# ── Test 5: Time series monotonically increasing ───────────────
print("\n[5] Time series monotonically increasing")
s = list(get_scenarios().values())[1]
ts = build_time_series(s, False, False, 30)
if len(ts) == 30:
    ok("Time series has 30 data points")
else:
    fail(f"Expected 30 points, got {len(ts)}")

estates = [row["Projected Estate"] for row in ts]
if all(estates[i] <= estates[i+1] for i in range(29)):
    ok(f"Estate grows monotonically yr1=${estates[0]:,.0f} → yr30=${estates[29]:,.0f}")
else:
    fail("Estate not monotonically increasing")

# ── Test 6: Insurance toggle on/off ───────────────────────────
print("\n[6] Insurance toggle")
e = EstateInputs(8_000_000, 0, 7_000_000, 100_000, 3_000_000, 0.06, 0.04, 10,
                 15_000_000, 0.40, 0.01, 0, 0.0, False)
r_no_ins = run_estate_model(e, False, False)
r_with_ins = run_estate_model(e, True, False)

if r_no_ins.insurance_offset == 0:
    ok("Insurance OFF: offset is zero")
else:
    fail(f"Insurance OFF but offset = ${r_no_ins.insurance_offset:,.0f}")

if r_with_ins.insurance_offset == 3_000_000:
    ok("Insurance ON: offset equals death benefit $3,000,000")
else:
    fail(f"Insurance ON: expected $3,000,000 offset, got ${r_with_ins.insurance_offset:,.0f}")

if r_with_ins.liquidity_shortfall < r_no_ins.liquidity_shortfall:
    ok("Insurance ON reduces liquidity shortfall")
else:
    fail("Insurance ON should reduce shortfall")

# ── Test 7: Risk labels ────────────────────────────────────────
print("\n[7] Risk label thresholds")
cases = [
    (0, 1_000_000, "Low"),
    (40_000, 1_000_000, "Low"),        # 4% — below 5% threshold
    (60_000, 1_000_000, "Moderate"),   # 6% — between 5% and 15%
    (200_000, 1_000_000, "High"),      # 20% — above 15%
]
for shortfall, estate, expected in cases:
    result = forced_sale_risk_label(shortfall, estate)
    if result == expected:
        ok(f"Risk label: shortfall/estate={shortfall/estate:.0%} → {result}")
    else:
        fail(f"Risk label: shortfall/estate={shortfall/estate:.0%} → got {result}, expected {expected}")

# ── Test 8: All scenarios pass basic sanity ────────────────────
print("\n[8] All scenarios basic sanity")
for name, inputs in get_scenarios().items():
    r = run_estate_model(inputs, True, True)
    errors = []
    if r.projected_net_estate < 0: errors.append("negative estate")
    if r.legacy_to_heirs < 0: errors.append("negative legacy")
    if r.total_settlement_costs < 0: errors.append("negative costs")
    if r.estimated_estate_tax < 0: errors.append("negative tax")
    if errors:
        fail(f"{name[:45]}: {', '.join(errors)}")
    else:
        ok(f"{name[:50]}")

# ── Summary ────────────────────────────────────────────────────
total = passed + failed
print(f"\n{'=' * 60}")
print(f"RESULT: {passed}/{total} tests passed", end="")
if failed == 0:
    print(" — ✓ ALL PASSED")
else:
    print(f" — ✗ {failed} FAILED")
print("=" * 60)
