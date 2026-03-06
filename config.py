# Mapping of JSON keys to Display Labels
TABLE_CONFIG = {
    "EMPLOYMENT": [
        ("subsidiary", "Subsidiary"),
        ("country", "Country"),
        ("start_date", "Start Date"),
        ("end_date", "End Date"),
        ("tenure_months", "Tenure (Months)"),
        ("savings_rate", "Savings Rate"),
        ("fx_rate_base_to_ref", "FX Rate (Base to Ref)"),
        # Client Income
        ("client_declared_income.total_pretax", "Client: Total Pre-tax"),
        ("client_declared_income.annualized_pretax", "Client: Annualized"),
        ("client_declared_income.monthly_pretax", "Client: Monthly"),
        ("client_declared_income.coverage_months", "Client: Coverage"),
        # Primary Income
        ("primary_corroboration_income.total_pretax", "Primary: Total Pre-tax"),
        ("primary_corroboration_income.annualized_pretax", "Primary: Annualized"),
        # Secondary Income
        ("secondary_corroboration_income.annualized_pretax_low", "Secondary: Annualized (Low)"),
        ("secondary_corroboration_income.annualized_pretax_high", "Secondary: Annualized (High)"),
    ],
    "GAP": [
        ("start_date", "Start Date"),
        ("end_date", "End Date"),
        ("duration_months", "Duration (Months)")
    ],
    "EQUITY_COMPENSATION": [
        ("employer", "Employer"),
        ("stock_options_value", "Stock Value"),
        ("stock_options_currency", "Currency"),
        ("grant_dates", "Grant Dates"),
        ("vesting_details", "Vesting Details"),
        ("equity_type", "Equity Type")
    ],
    "ADDITIONAL_NOTES": [
        ("notes", "General Notes")
    ]
}
