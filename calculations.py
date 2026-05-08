from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class EstateInputs:
    current_real_estate_value: float
    current_debt: float
    other_assets: float
    liquid_assets: float
    life_insurance_death_benefit: float
    real_estate_appreciation_rate: float
    other_asset_growth_rate: float
    years_until_death: int
    estate_tax_exemption: float
    estate_tax_rate: float
    probate_cost_rate: float
    gifting_reduction_percent: float
    # NEW: FLP valuation discount (default 0 = no discount, matches original behavior)
    flp_valuation_discount: float = 0.0
    # NEW: Whether insurance is held in ILIT (outside taxable estate)
    insurance_in_ilit: bool = False


@dataclass
class EstateResults:
    projected_real_estate_value: float
    projected_other_assets: float
    projected_gross_estate: float
    projected_net_estate: float
    gifting_reduction_amount: float
    taxable_estate: float
    estimated_estate_tax: float
    estimated_probate_cost: float
    total_settlement_costs: float
    available_liquidity: float
    insurance_offset: float
    liquidity_shortfall: float
    legacy_to_heirs: float


def future_value(principal: float, annual_rate: float, years: int) -> float:
    return principal * ((1 + annual_rate) ** years)


def project_estate_value(inputs: EstateInputs) -> tuple[float, float, float, float]:
    projected_real_estate = future_value(
        inputs.current_real_estate_value,
        inputs.real_estate_appreciation_rate,
        inputs.years_until_death,
    )
    projected_other_assets = future_value(
        inputs.other_assets,
        inputs.other_asset_growth_rate,
        inputs.years_until_death,
    )
    projected_gross_estate = projected_real_estate + projected_other_assets
    # If insurance is personally owned (not ILIT), death benefit is included in taxable estate
    projected_net_estate = max(projected_gross_estate - inputs.current_debt, 0.0)
    return projected_real_estate, projected_other_assets, projected_gross_estate, projected_net_estate


def estimate_gifting_reduction(
    projected_net_estate: float,
    gifting_reduction_percent: float,
    flp_valuation_discount: float = 0.0,
) -> float:
    """
    FLP two-step math:
      Step 1: gross gift amount = projected estate * gifting %
      Step 2: apply valuation discount → taxable gift = gross gift * (1 - discount)
      The REDUCTION to the taxable estate equals the discounted gift value.
    When discount = 0, this collapses to the original simple slider behavior.
    """
    gifting_reduction_percent = min(max(gifting_reduction_percent, 0.0), 1.0)
    flp_valuation_discount = min(max(flp_valuation_discount, 0.0), 0.50)
    gross_gift = projected_net_estate * gifting_reduction_percent
    discounted_gift = gross_gift * (1.0 - flp_valuation_discount)
    return discounted_gift


def estimate_taxable_estate(
    projected_net_estate: float,
    estate_tax_exemption: float,
    gifting_reduction_amount: float = 0.0,
    insurance_death_benefit: float = 0.0,
    insurance_in_ilit: bool = False,
) -> float:
    """
    If insurance is personally owned, its death benefit is INCLUDED in the taxable estate.
    If insurance is in an ILIT, it is EXCLUDED from the taxable estate.
    """
    insurance_in_estate = 0.0 if insurance_in_ilit else insurance_death_benefit
    taxable = (
        projected_net_estate
        + insurance_in_estate
        - gifting_reduction_amount
        - estate_tax_exemption
    )
    return max(taxable, 0.0)


def estimate_settlement_costs(
    projected_net_estate: float,
    taxable_estate: float,
    estate_tax_rate: float,
    probate_cost_rate: float,
) -> tuple[float, float, float]:
    estimated_estate_tax = max(taxable_estate * estate_tax_rate, 0.0)
    estimated_probate_cost = max(projected_net_estate * probate_cost_rate, 0.0)
    total_settlement_costs = estimated_estate_tax + estimated_probate_cost
    return estimated_estate_tax, estimated_probate_cost, total_settlement_costs


def estimate_liquidity_gap(
    liquid_assets: float,
    life_insurance_death_benefit: float,
    total_settlement_costs: float,
    include_insurance: bool,
) -> tuple[float, float, float]:
    insurance_offset = life_insurance_death_benefit if include_insurance else 0.0
    available_liquidity = liquid_assets + insurance_offset
    liquidity_shortfall = max(total_settlement_costs - available_liquidity, 0.0)
    return available_liquidity, insurance_offset, liquidity_shortfall


def estimate_legacy_to_heirs(
    projected_net_estate: float,
    total_settlement_costs: float,
    gifting_reduction_amount: float = 0.0,
    include_gifting_as_legacy: bool = True,
) -> float:
    estate_after_costs = max(projected_net_estate - total_settlement_costs, 0.0)
    if include_gifting_as_legacy:
        return estate_after_costs + gifting_reduction_amount
    return estate_after_costs


def forced_sale_risk_label(liquidity_shortfall: float, projected_net_estate: float) -> str:
    if projected_net_estate <= 0:
        return "Unknown"
    ratio = liquidity_shortfall / projected_net_estate
    if ratio <= 0.05:
        return "Low"
    if ratio <= 0.15:
        return "Moderate"
    return "High"


def run_estate_model(
    inputs: EstateInputs,
    include_insurance: bool,
    include_gifting: bool,
) -> EstateResults:
    projected_real_estate, projected_other_assets, projected_gross_estate, projected_net_estate = (
        project_estate_value(inputs)
    )

    gifting_reduction_amount = (
        estimate_gifting_reduction(
            projected_net_estate,
            inputs.gifting_reduction_percent,
            inputs.flp_valuation_discount,
        )
        if include_gifting
        else 0.0
    )

    taxable_estate = estimate_taxable_estate(
        projected_net_estate=projected_net_estate,
        estate_tax_exemption=inputs.estate_tax_exemption,
        gifting_reduction_amount=gifting_reduction_amount,
        insurance_death_benefit=inputs.life_insurance_death_benefit,
        insurance_in_ilit=inputs.insurance_in_ilit if include_insurance else False,
    )

    estimated_estate_tax, estimated_probate_cost, total_settlement_costs = estimate_settlement_costs(
        projected_net_estate=projected_net_estate,
        taxable_estate=taxable_estate,
        estate_tax_rate=inputs.estate_tax_rate,
        probate_cost_rate=inputs.probate_cost_rate,
    )

    available_liquidity, insurance_offset, liquidity_shortfall = estimate_liquidity_gap(
        liquid_assets=inputs.liquid_assets,
        life_insurance_death_benefit=inputs.life_insurance_death_benefit,
        total_settlement_costs=total_settlement_costs,
        include_insurance=include_insurance,
    )

    legacy_to_heirs = estimate_legacy_to_heirs(
        projected_net_estate=projected_net_estate,
        total_settlement_costs=total_settlement_costs,
        gifting_reduction_amount=gifting_reduction_amount,
        include_gifting_as_legacy=include_gifting,
    )

    return EstateResults(
        projected_real_estate_value=projected_real_estate,
        projected_other_assets=projected_other_assets,
        projected_gross_estate=projected_gross_estate,
        projected_net_estate=projected_net_estate,
        gifting_reduction_amount=gifting_reduction_amount,
        taxable_estate=taxable_estate,
        estimated_estate_tax=estimated_estate_tax,
        estimated_probate_cost=estimated_probate_cost,
        total_settlement_costs=total_settlement_costs,
        available_liquidity=available_liquidity,
        insurance_offset=insurance_offset,
        liquidity_shortfall=liquidity_shortfall,
        legacy_to_heirs=legacy_to_heirs,
    )


def build_time_series(
    inputs: EstateInputs,
    include_insurance: bool,
    include_gifting: bool,
    max_years: int = 30,
) -> list[dict]:
    """
    Returns a list of dicts, one per year from 1 to max_years,
    with projected estate, settlement costs, and legacy to heirs.
    Used for the time-series chart.
    """
    rows = []
    for yr in range(1, max_years + 1):
        yr_inputs = EstateInputs(
            current_real_estate_value=inputs.current_real_estate_value,
            current_debt=inputs.current_debt,
            other_assets=inputs.other_assets,
            liquid_assets=inputs.liquid_assets,
            life_insurance_death_benefit=inputs.life_insurance_death_benefit,
            real_estate_appreciation_rate=inputs.real_estate_appreciation_rate,
            other_asset_growth_rate=inputs.other_asset_growth_rate,
            years_until_death=yr,
            estate_tax_exemption=inputs.estate_tax_exemption,
            estate_tax_rate=inputs.estate_tax_rate,
            probate_cost_rate=inputs.probate_cost_rate,
            gifting_reduction_percent=inputs.gifting_reduction_percent,
            flp_valuation_discount=inputs.flp_valuation_discount,
            insurance_in_ilit=inputs.insurance_in_ilit,
        )
        r = run_estate_model(yr_inputs, include_insurance, include_gifting)
        rows.append({
            "Year": yr,
            "Projected Estate": r.projected_net_estate,
            "Settlement Costs": r.total_settlement_costs,
            "Legacy to Heirs": r.legacy_to_heirs,
            "Liquidity Shortfall": r.liquidity_shortfall,
        })
    return rows
