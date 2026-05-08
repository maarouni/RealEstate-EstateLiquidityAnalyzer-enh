import hmac
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from calculations import EstateInputs, run_estate_model, forced_sale_risk_label, build_time_series
from scenarios import get_scenarios
from labels import *
from disclaimer import DISCLAIMER_TEXT

st.set_page_config(page_title=APP_TITLE, layout="wide")


# ─────────────────────────────────────────────────────────────────
# Layer 1: Master password gate
# ─────────────────────────────────────────────────────────────────
def check_password():
    def password_entered():
        if hmac.compare_digest(st.session_state["password"], st.secrets["password"]):
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if st.session_state.get("password_correct", False):
        return True

    st.markdown("### Estate Liquidity Analyzer")
    st.text_input("Password", type="password", on_change=password_entered, key="password")
    if "password_correct" in st.session_state:
        st.error("Incorrect password")
    return False


if not check_password():
    st.stop()


# ─────────────────────────────────────────────────────────────────
# Layer 2: Per-user PIN gate
# pins stored in secrets as: [pins] user1 = "1234" user2 = "5678"
# ─────────────────────────────────────────────────────────────────
def check_pin():
    def pin_entered():
        entered_pin = st.session_state.get("pin_input", "").strip()
        valid_pins = st.secrets.get("pins", {})
        matched_user = None
        for user, pin in valid_pins.items():
            if hmac.compare_digest(entered_pin, str(pin)):
                matched_user = user
                break
        if matched_user:
            st.session_state["pin_correct"] = True
            st.session_state["pin_user"] = matched_user
            if "pin_input" in st.session_state:
                del st.session_state["pin_input"]
        else:
            st.session_state["pin_correct"] = False

    if st.session_state.get("pin_correct", False):
        return True

    st.markdown("### Enter Your PIN")
    st.caption("Each user has a unique PIN. Contact the administrator if you need access.")
    st.text_input("PIN", type="password", on_change=pin_entered, key="pin_input",
                  placeholder="Enter your PIN")
    if "pin_correct" in st.session_state and not st.session_state["pin_correct"]:
        st.error("Invalid PIN. Please try again or contact the administrator.")
    return False


if not check_pin():
    st.stop()

# Show logged-in user quietly in sidebar
if st.session_state.get("pin_user"):
    st.sidebar.caption(f"Logged in as: {st.session_state['pin_user']}")


# ─────────────────────────────────────────────────────────────────
# Title
# ─────────────────────────────────────────────────────────────────
st.title(APP_TITLE)
st.caption(APP_SUBTITLE)

with st.container():
    st.markdown(
        """<div style='background-color:#1a3a5c;padding:12px 16px;border-radius:6px;border-left:4px solid #4472C4;'>
        <span style='font-size:15px;color:#ffffff;'>
        ⚖️ <strong>2026 Tax Law Update — OBBBA:</strong> 
        The federal estate tax exemption is now 
        <strong>$15,000,000 per individual ($30,000,000 for married couples)</strong>, 
        effective January 1, 2026. 
        The prior TCJA sunset to ~$7M was permanently eliminated by the 
        One Big Beautiful Bill Act (OBBBA), signed July 4, 2025. 
        The 40% estate tax rate on amounts above the exemption remains unchanged. 
        All scenarios in this tool reflect current 2026 law.
        </span></div>""",
        unsafe_allow_html=True
    )

scenarios = get_scenarios()
scenario_name = st.selectbox("Select Client Scenario", list(scenarios.keys()))
selected = scenarios[scenario_name]

# Scenario descriptions
scenario_descriptions = {
    "HNW RE Investor — FLP + ILIT Combined Strategy": (
        "**HNW RE Investor — FLP + ILIT Combined Strategy.** "
        "Starting point for a Bay Area real estate investor with significant property holdings and an estate tax exposure horizon. "
        "Adjust all fields to match your client's actual situation. "
        "FLP valuation discount and ILIT structure are pre-enabled — turn off if not applicable."
    ),
    "Base Case": (
        "**Base Case.** "
        "A mid-range investor profile with moderate real estate holdings, some debt, and existing life insurance. "
        "No FLP or ILIT structure enabled. Use as a clean starting point before layering in planning strategies."
    ),
    "High Growth / Low Liquidity": (
        "**High Growth / Low Liquidity.** "
        "A client with a rapidly appreciating real estate portfolio but minimal liquid assets and limited insurance coverage. "
        "Illustrates the forced-sale risk that emerges when estate growth outpaces liquidity planning."
    ),
    "Insurance Solves the Gap": (
        "**Insurance Solves the Gap.** "
        "A client with a meaningful liquidity shortfall that is fully addressed by a large life insurance death benefit. "
        "Demonstrates how insurance alone — without gifting — can close the estate tax liquidity gap."
    ),
    "Planning Reduces Taxable Estate": (
        "**Planning Reduces Taxable Estate.** "
        "A high-value estate where gifting and entity planning significantly reduce the taxable estate. "
        "Shows how estate reduction strategies lower the tax bill even before insurance is introduced."
    ),
}
if scenario_name in scenario_descriptions:
    st.info(scenario_descriptions[scenario_name])

st.markdown(f"### {SECTION_INPUTS}")

col1, col2 = st.columns(2)

with col1:
    current_real_estate_value = st.number_input(
        LABEL_CURRENT_RE_VALUE,
        min_value=0.0,
        value=float(selected.current_real_estate_value),
        step=100000.0,
        format="%.0f",
    )
    current_debt = st.number_input(
        LABEL_CURRENT_DEBT,
        min_value=0.0,
        value=float(selected.current_debt),
        step=50000.0,
        format="%.0f",
    )
    other_assets = st.number_input(
        LABEL_OTHER_ASSETS,
        min_value=0.0,
        value=float(selected.other_assets),
        step=100000.0,
        format="%.0f",
    )
    liquid_assets = st.number_input(
        LABEL_LIQUID_ASSETS,
        min_value=0.0,
        value=float(selected.liquid_assets),
        step=50000.0,
        format="%.0f",
    )
    life_insurance_death_benefit = st.number_input(
        LABEL_INSURANCE,
        min_value=0.0,
        value=float(selected.life_insurance_death_benefit),
        step=100000.0,
        format="%.0f",
    )
    years_until_death = st.slider(
        LABEL_YEARS,
        min_value=1,
        max_value=30,
        value=int(selected.years_until_death),
    )

with col2:
    real_estate_appreciation_rate = st.slider(
        LABEL_RE_APPRECIATION,
        min_value=0.0,
        max_value=10.0,
        value=float(selected.real_estate_appreciation_rate * 100),
        step=0.1,
    ) / 100.0
    other_asset_growth_rate = st.slider(
        LABEL_OTHER_GROWTH,
        min_value=0.0,
        max_value=10.0,
        value=float(selected.other_asset_growth_rate * 100),
        step=0.1,
    ) / 100.0
    estate_tax_exemption = st.number_input(
        LABEL_EXEMPTION,
        min_value=0.0,
        value=float(selected.estate_tax_exemption),
        step=100000.0,
        format="%.0f",
    )
    estate_tax_rate = st.slider(
        LABEL_TAX_RATE,
        min_value=0.0,
        max_value=60.0,
        value=float(selected.estate_tax_rate * 100),
        step=0.5,
    ) / 100.0
    probate_cost_rate = st.slider(
        LABEL_PROBATE_RATE,
        min_value=0.0,
        max_value=10.0,
        value=float(selected.probate_cost_rate * 100),
        step=0.1,
    ) / 100.0
    gifting_reduction_percent = st.slider(
        LABEL_GIFTING_REDUCTION,
        min_value=0.0,
        max_value=80.0,
        value=float(selected.gifting_reduction_percent * 100),
        step=1.0,
    ) / 100.0

# ─────────────────────────────────────────────────────────────────
# ENHANCEMENT 1 & 2: FLP Valuation Discount + ILIT Toggle
# ─────────────────────────────────────────────────────────────────
st.markdown("### FLP & Insurance Structure")
flp_col, ilit_col = st.columns(2)

with flp_col:
    flp_valuation_discount = st.slider(
        LABEL_FLP_DISCOUNT,
        min_value=0.0,
        max_value=50.0,
        value=float(selected.flp_valuation_discount * 100),
        step=1.0,
        help=FLP_HELP,
    ) / 100.0
    # Show effective gift calculation live
    if gifting_reduction_percent > 0 and flp_valuation_discount > 0:
        gross_gift_pct = gifting_reduction_percent * 100
        net_gift_pct = gifting_reduction_percent * (1 - flp_valuation_discount) * 100
        st.caption(
            f"FLP math: {gross_gift_pct:.0f}% gifted × "
            f"{(1 - flp_valuation_discount)*100:.0f}% after {flp_valuation_discount*100:.0f}% discount "
            f"= **{net_gift_pct:.1f}% effective estate reduction**"
        )

with ilit_col:
    insurance_in_ilit = st.checkbox(
        LABEL_ILIT,
        value=bool(selected.insurance_in_ilit),
        help=ILIT_HELP,
    )
    if insurance_in_ilit:
        st.caption(
            "✅ ILIT: Death benefit is **excluded** from the taxable estate — "
            "proceeds pass to heirs outside of estate taxation."
        )
    else:
        st.caption(
            "⚠️ Personally owned: Death benefit is **included** in the taxable estate — "
            "increases estate tax exposure."
        )

# ─────────────────────────────────────────────────────────────────
# Planning toggles — identical to original
# ─────────────────────────────────────────────────────────────────
st.markdown(f"### {SECTION_TOGGLES}")
toggle_col1, toggle_col2 = st.columns(2)

with toggle_col1:
    include_insurance = st.checkbox(LABEL_INCLUDE_INSURANCE, value=True)

with toggle_col2:
    include_gifting = st.checkbox(LABEL_INCLUDE_GIFTING, value=True)

# ─────────────────────────────────────────────────────────────────
# Build inputs object
# ─────────────────────────────────────────────────────────────────
inputs = EstateInputs(
    current_real_estate_value=current_real_estate_value,
    current_debt=current_debt,
    other_assets=other_assets,
    liquid_assets=liquid_assets,
    life_insurance_death_benefit=life_insurance_death_benefit,
    real_estate_appreciation_rate=real_estate_appreciation_rate,
    other_asset_growth_rate=other_asset_growth_rate,
    years_until_death=years_until_death,
    estate_tax_exemption=estate_tax_exemption,
    estate_tax_rate=estate_tax_rate,
    probate_cost_rate=probate_cost_rate,
    gifting_reduction_percent=gifting_reduction_percent,
    flp_valuation_discount=flp_valuation_discount,
    insurance_in_ilit=insurance_in_ilit,
)

results = run_estate_model(
    inputs=inputs,
    include_insurance=include_insurance,
    include_gifting=include_gifting,
)

risk = forced_sale_risk_label(
    results.liquidity_shortfall,
    results.projected_net_estate,
)

# ─────────────────────────────────────────────────────────────────
# Results metrics — identical layout to original
# ─────────────────────────────────────────────────────────────────
st.markdown(f"### {SECTION_RESULTS}")

m1, m2, m3 = st.columns(3)
m4, m5, m6 = st.columns(3)

m1.metric(RESULT_PROJECTED_NET_ESTATE, f"${results.projected_net_estate:,.0f}")
m2.metric(RESULT_TAXABLE_ESTATE, f"${results.taxable_estate:,.0f}")
m3.metric(RESULT_SETTLEMENT_COSTS, f"${results.total_settlement_costs:,.0f}")
m4.metric(RESULT_INSURANCE_OFFSET, f"${results.insurance_offset:,.0f}")
m5.metric(RESULT_LIQUIDITY_SHORTFALL, f"${results.liquidity_shortfall:,.0f}")
m6.metric(RESULT_LEGACY_TO_HEIRS, f"${results.legacy_to_heirs:,.0f}")

st.info(f"{RESULT_RISK}: **{risk}**")

# ─────────────────────────────────────────────────────────────────
# Planning Comparison Snapshot — identical logic + color to original
# ─────────────────────────────────────────────────────────────────
st.markdown("### Planning Comparison Snapshot")
st.caption(
    "Compare how different planning strategies impact liquidity, settlement costs, and legacy outcomes."
)

comparison_cases = {
    "Current Planning": run_estate_model(inputs, include_insurance=False, include_gifting=False),
    "Insurance Only": run_estate_model(inputs, include_insurance=True, include_gifting=False),
    "Gifting / FLP Only": run_estate_model(inputs, include_insurance=False, include_gifting=True),
    "Insurance + Gifting": run_estate_model(inputs, include_insurance=True, include_gifting=True),
}

comparison_rows = []
for case_name, case_result in comparison_cases.items():
    case_risk = forced_sale_risk_label(case_result.liquidity_shortfall, case_result.projected_net_estate)

    if case_name == "Current Planning":
        outcome = "Significant liquidity exposure"
    elif case_name == "Insurance Only":
        outcome = "Improves liquidity position"
    elif case_name == "Gifting / FLP Only":
        outcome = (
            "Reduces estate and supports liquidity"
            if case_result.liquidity_shortfall <= 0
            else "Reduces estate, but liquidity gap remains"
        )
    elif case_name == "Insurance + Gifting":
        if case_result.liquidity_shortfall <= 0:
            outcome = "Optimizes liquidity and legacy"
        else:
            outcome = "Best overall — gap materially reduced"
    else:
        outcome = "Planning impact shown"

    comparison_rows.append({
        "Scenario": case_name,
        "Settlement Costs": case_result.total_settlement_costs,
        "Insurance Offset": case_result.insurance_offset,
        "Liquidity Shortfall": case_result.liquidity_shortfall,
        "Legacy to Heirs": case_result.legacy_to_heirs,
        "Risk": case_risk,
        "Outcome": outcome,
    })

comparison_df = pd.DataFrame(comparison_rows)


# Color styling — identical to original
def highlight_risk(val):
    if val == "Low":
        return "background-color: #163d1a; color: #7CFC00;"
    elif val == "Moderate":
        return "background-color: #4a3b00; color: #FFD700;"
    elif val == "High":
        return "background-color: #4a0f0f; color: #FF6B6B;"
    return ""


def highlight_shortfall(val):
    try:
        val = float(val)
        if val <= 0:
            return "background-color: #163d1a; color: #7CFC00;"
        elif val < 250000:
            return "background-color: #4a3b00; color: #FFD700;"
        else:
            return "background-color: #4a0f0f; color: #FF6B6B;"
    except Exception:
        return ""


def highlight_outcome(val):
    if "Optimizes" in val:
        return "background-color: #163d1a; color: #7CFC00;"
    elif "Improves" in val or "Reduces" in val or "supports" in val:
        return "background-color: #1a2f4a; color: #87CEFA;"
    elif "gap remains" in val:
        return "background-color: #4a3b00; color: #FFD700;"
    elif "Significant" in val:
        return "background-color: #4a0f0f; color: #FF6B6B;"
    return ""


styled_comparison_df = (
    comparison_df.style
    .format({
        "Settlement Costs": "${:,.0f}",
        "Insurance Offset": "${:,.0f}",
        "Liquidity Shortfall": "${:,.0f}",
        "Legacy to Heirs": "${:,.0f}",
    })
    .map(highlight_risk, subset=["Risk"])
    .map(highlight_shortfall, subset=["Liquidity Shortfall"])
    .map(highlight_outcome, subset=["Outcome"])
)

st.write(styled_comparison_df.to_html(), unsafe_allow_html=True)

# Best strategy callout — single clean line
best_case = comparison_df.sort_values("Liquidity Shortfall", ascending=True).iloc[0]
best_scenario = best_case['Scenario']
best_costs = best_case['Settlement Costs']
best_legacy = best_case['Legacy to Heirs']
st.caption(f"Best outcome: **{best_scenario}** — Settlement Costs ${best_costs:,.0f} | Legacy to Heirs ${best_legacy:,.0f}")

# ─────────────────────────────────────────────────────────────────
# ENHANCEMENT 3: Time-Series Chart — Legacy over 1–30 years
# ─────────────────────────────────────────────────────────────────
st.markdown(f"### {SECTION_TIMESERIES}")
st.caption(
    "Shows how the estate, settlement costs, and legacy to heirs evolve over time "
    "under the currently selected planning strategy. "
    "The vertical line marks the selected 'years until death' horizon."
)

time_series_data = build_time_series(
    inputs=inputs,
    include_insurance=include_insurance,
    include_gifting=include_gifting,
    max_years=30,
)
ts_df = pd.DataFrame(time_series_data)

fig = go.Figure()

fig.add_trace(go.Scatter(
    x=ts_df["Year"], y=ts_df["Projected Estate"],
    mode="lines", name="Projected Estate",
    line=dict(color="#4472C4", width=2),
))
fig.add_trace(go.Scatter(
    x=ts_df["Year"], y=ts_df["Settlement Costs"],
    mode="lines", name="Settlement Costs",
    line=dict(color="#FF6B6B", width=2, dash="dash"),
))
fig.add_trace(go.Scatter(
    x=ts_df["Year"], y=ts_df["Legacy to Heirs"],
    mode="lines", name="Legacy to Heirs",
    line=dict(color="#7CFC00", width=2),
    fill="tozeroy",
    fillcolor="rgba(124,252,0,0.08)",
))
fig.add_trace(go.Scatter(
    x=ts_df["Year"], y=ts_df["Liquidity Shortfall"],
    mode="lines", name="Liquidity Shortfall",
    line=dict(color="#FFD700", width=2, dash="dot"),
))

# Vertical marker at selected year
fig.add_vline(
    x=years_until_death,
    line_dash="dot",
    line_color="white",
    line_width=1,
    annotation_text=f"Year {years_until_death}",
    annotation_position="top right",
    annotation_font_color="white",
)

fig.update_layout(
    template="plotly_dark",
    title="Estate & Legacy Trajectory (Years 1–30)",
    xaxis_title="Years from Now",
    yaxis_title="Value ($)",
    yaxis_tickformat="$,.0f",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    hovermode="x unified",
    height=450,
)

st.plotly_chart(fig, width="stretch")

# ─────────────────────────────────────────────────────────────────
# Original bar chart snapshot — kept as-is
# ─────────────────────────────────────────────────────────────────
summary_df = pd.DataFrame({
    "Metric": [
        "Projected Real Estate Value",
        "Projected Other Assets",
        "Projected Gross Estate",
        "Projected Net Estate",
        "Gifting Reduction Amount",
        "Estimated Estate Tax",
        "Estimated Probate Cost",
        "Total Settlement Costs",
        "Available Liquidity",
        "Insurance Offset",
        "Liquidity Shortfall",
        "Legacy to Heirs",
    ],
    "Value": [
        results.projected_real_estate_value,
        results.projected_other_assets,
        results.projected_gross_estate,
        results.projected_net_estate,
        results.gifting_reduction_amount,
        results.estimated_estate_tax,
        results.estimated_probate_cost,
        results.total_settlement_costs,
        results.available_liquidity,
        results.insurance_offset,
        results.liquidity_shortfall,
        results.legacy_to_heirs,
    ],
})

chart = px.bar(summary_df, x="Metric", y="Value", title="Estate Liquidity Snapshot")
st.plotly_chart(chart, width="stretch")

with st.expander("See detailed calculation table"):
    display_df = summary_df.copy()
    display_df["Value"] = display_df["Value"].map(lambda x: f"${x:,.0f}")
    st.dataframe(display_df, width="stretch")

# ─────────────────────────────────────────────────────────────────
# Formula Methodology — credibility section for Aaron
# ─────────────────────────────────────────────────────────────────
with st.expander(f"📐 {SECTION_METHODOLOGY} — Formula Sources & Assumptions"):
    st.markdown("""
| Formula | Expression | Source / Authority |
|---|---|---|
| Future estate value | `PV × (1 + r)^n` | Standard compound growth — CCIM curriculum, Finance 101 |
| Estate tax | `Taxable Estate × 40%` | IRC Section 2001 — federal marginal rate (unchanged by OBBBA) |
| Probate / settlement cost | `Net Estate × 1%` | NYL APG standard illustration assumption (matched exactly) |
| FLP gifting reduction | `Estate × % Gifted × (1 − Valuation Discount)` | IRC Sections 2036/2038 — standard valuation discount methodology |
| Taxable estate (ILIT) | Excludes death benefit from taxable estate | IRC Section 2042 — ILIT removes policy from taxable estate |
| Taxable estate (personally owned) | Includes death benefit in taxable estate | IRC Section 2042 |
| Liquidity shortfall | `Settlement Costs − (Liquid Assets + Insurance Offset)` | Standard estate liquidity analysis framework |
| Legacy to heirs | `Net Estate − Settlement Costs + Gifted Assets` | Standard estate planning illustration methodology |

**Estate Tax Exemption — 2026 current law:** USD 15,000,000 per individual per the One Big Beautiful Bill Act (OBBBA), signed July 4, 2025. Permanent, indexed for inflation from 2027. For married couples: USD 30M combined. The prior sunset to approx. USD 7M was eliminated by OBBBA.

**Assumptions that are estimates (not law-sourced):**
- RE appreciation rate default 6%: based on Bay Area long-term average — adjust to client's specific market
- Other asset growth rate default 5%: general market estimate — adjust to client's portfolio
- Forced sale risk thresholds (Low/Moderate/High): shortfall-to-estate ratios of 2%/8% are illustrative heuristics, not industry-standard definitions
- FLP valuation discount: industry standard is 20–35%; IRS typically challenges discounts above 35–40%; default 30% matches NYL APG illustration

*All outputs are educational illustrations only. Not legal, tax, or accounting advice.*
    """)

# ─────────────────────────────────────────────────────────────────
# Disclaimer — identical to original
# ─────────────────────────────────────────────────────────────────
st.markdown(f"### {SECTION_DISCLAIMER}")
st.caption(DISCLAIMER_TEXT)
