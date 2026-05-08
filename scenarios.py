from calculations import EstateInputs


def get_scenarios() -> dict[str, EstateInputs]:
    return {
        # ─────────────────────────────────────────────────────────────────
        # NEW: HNW RE Investor profile — anonymized from APG reference case
        # $11.7M estate, $6.1M in RE investments, 10-year horizon
        # Mirrors the NYL APG illustration for cross-validation
        # ─────────────────────────────────────────────────────────────────
        "HNW RE Investor — FLP + ILIT Combined Strategy": EstateInputs(
            current_real_estate_value=4_000_000,   # typical Bay Area RE portfolio — advisor adjusts
            current_debt=500_000,
            other_assets=2_000_000,                # other investments, savings
            liquid_assets=300_000,
            life_insurance_death_benefit=1_000_000, # existing policy — advisor adjusts
            real_estate_appreciation_rate=0.06,     # Bay Area long-term avg
            other_asset_growth_rate=0.05,
            years_until_death=10,
            estate_tax_exemption=15_000_000,        # OBBBA 2026: $15M permanent exemption (signed July 4, 2025)
            estate_tax_rate=0.40,
            probate_cost_rate=0.01,
            gifting_reduction_percent=0.80,         # FLP: 80% gifted
            flp_valuation_discount=0.30,            # 30% valuation discount
            insurance_in_ilit=True,                 # ILIT structure enabled
        ),
        # ─────────────────────────────────────────────────────────────────
        # Original scenarios preserved exactly as-is
        # ─────────────────────────────────────────────────────────────────
        "Base Case": EstateInputs(
            current_real_estate_value=8_000_000,   # Bay Area multi-property portfolio
            current_debt=1_500_000,
            other_assets=5_000_000,
            liquid_assets=500_000,
            life_insurance_death_benefit=1_500_000,
            real_estate_appreciation_rate=0.05,
            other_asset_growth_rate=0.04,
            years_until_death=12,
            estate_tax_exemption=15_000_000,  # OBBBA 2026: $15M permanent exemption
            estate_tax_rate=0.40,
            probate_cost_rate=0.01,
            gifting_reduction_percent=0.20,
            flp_valuation_discount=0.0,
            insurance_in_ilit=False,
        ),
        "High Growth / Low Liquidity": EstateInputs(
            current_real_estate_value=10_000_000,  # Large appreciating portfolio, illiquid
            current_debt=2_000_000,
            other_assets=3_000_000,
            liquid_assets=200_000,                 # Very low liquidity — the stress point
            life_insurance_death_benefit=500_000,
            real_estate_appreciation_rate=0.07,    # High appreciation assumption
            other_asset_growth_rate=0.05,
            years_until_death=12,
            estate_tax_exemption=15_000_000,  # OBBBA 2026: $15M permanent exemption
            estate_tax_rate=0.40,
            probate_cost_rate=0.012,
            gifting_reduction_percent=0.10,
            flp_valuation_discount=0.0,
            insurance_in_ilit=False,
        ),
        "Insurance Solves the Gap": EstateInputs(
            current_real_estate_value=9_000_000,   # Large estate approaching exemption threshold
            current_debt=1_000_000,
            other_assets=5_000_000,
            liquid_assets=150_000,                 # Minimal liquidity
            life_insurance_death_benefit=4_000_000, # Large policy closes the gap
            real_estate_appreciation_rate=0.06,
            other_asset_growth_rate=0.04,
            years_until_death=10,
            estate_tax_exemption=15_000_000,  # OBBBA 2026: $15M permanent exemption
            estate_tax_rate=0.40,
            probate_cost_rate=0.01,
            gifting_reduction_percent=0.10,
            flp_valuation_discount=0.0,
            insurance_in_ilit=False,
        ),
        "Planning Reduces Taxable Estate": EstateInputs(
            current_real_estate_value=12_000_000,  # Large estate clearly above $15M threshold at growth
            current_debt=2_000_000,
            other_assets=6_000_000,
            liquid_assets=400_000,
            life_insurance_death_benefit=1_000_000,
            real_estate_appreciation_rate=0.06,
            other_asset_growth_rate=0.04,
            years_until_death=10,
            estate_tax_exemption=15_000_000,  # OBBBA 2026: $15M permanent exemption
            estate_tax_rate=0.40,
            probate_cost_rate=0.01,
            gifting_reduction_percent=0.30,    # FLP gifting reduces taxable estate significantly
            flp_valuation_discount=0.0,
            insurance_in_ilit=False,
        ),
    }
