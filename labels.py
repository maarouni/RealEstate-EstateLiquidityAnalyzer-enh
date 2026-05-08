APP_TITLE = "Estate Liquidity Analyzer"
APP_SUBTITLE = "Prototype for modeling estate liquidity, settlement costs, insurance offset, and legacy impact."

SECTION_INPUTS = "Client / Estate Inputs"
SECTION_TOGGLES = "Planning Options"
SECTION_RESULTS = "Model Results"
SECTION_SCENARIOS = "Scenario Presets"
SECTION_DISCLAIMER = "Important Disclaimer"
SECTION_TIMESERIES = "Legacy Over Time"
SECTION_METHODOLOGY = "Formula Methodology"

LABEL_CURRENT_RE_VALUE = "Current Real Estate Value ($)"
LABEL_CURRENT_DEBT = "Current Debt ($)"
LABEL_OTHER_ASSETS = "Other Assets ($)"
LABEL_LIQUID_ASSETS = "Liquid Assets Available ($)"
LABEL_INSURANCE = "Life Insurance Death Benefit ($)"
LABEL_RE_APPRECIATION = "Real Estate Appreciation Rate (%)"
LABEL_OTHER_GROWTH = "Other Asset Growth Rate (%)"
LABEL_YEARS = "Years Until Death"
LABEL_EXEMPTION = "Estate Tax Exemption ($)"
LABEL_TAX_RATE = "Estate Tax Rate (%)"
LABEL_PROBATE_RATE = "Probate / Settlement Cost Rate (%)"
LABEL_GIFTING_REDUCTION = "Gifting % — Portion of Estate Transferred via FLP/Gift"
LABEL_FLP_DISCOUNT = "FLP Valuation Discount (%) — Discount applied to gifted LP shares"
LABEL_ILIT = "Insurance held in ILIT (outside taxable estate)"

LABEL_INCLUDE_INSURANCE = "Include insurance offset"
LABEL_INCLUDE_GIFTING = "Include gifting / FLP planning reduction"

RESULT_PROJECTED_NET_ESTATE = "Projected Net Estate"
RESULT_TAXABLE_ESTATE = "Taxable Estate"
RESULT_SETTLEMENT_COSTS = "Settlement Costs"
RESULT_INSURANCE_OFFSET = "Insurance Offset"
RESULT_LIQUIDITY_SHORTFALL = "Liquidity Shortfall"
RESULT_LEGACY_TO_HEIRS = "Legacy to Heirs"
RESULT_RISK = "Forced Sale Risk"

ILIT_HELP = (
    "ILIT = Irrevocable Life Insurance Trust. "
    "When checked, the death benefit is excluded from the taxable estate. "
    "When unchecked, the death benefit is included in the taxable estate and increases the tax burden."
)
FLP_HELP = (
    "FLP = Family Limited Partnership. "
    "A valuation discount (typically 20–40%) is applied to gifted LP shares because they lack "
    "marketability and control. This reduces the taxable gift below the face value of assets transferred. "
    "Set to 0% if not using an FLP structure."
)
