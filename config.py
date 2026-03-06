# Configuration for table fields in each section
# Format: (JSON_KEY, DISPLAY_LABEL)

TABLE_CONFIG = {
    "EMPLOYMENT": [
        ("subsidiary", "Subsidiary"),
        ("country", "Country"),
        ("dates", "Period"),
        ("client_declared_income.annualized_pretax", "Annualized (Client)"),
        ("primary_corroboration_income.annualized_pretax", "Annualized (Primary)"),
        ("client_declared_income.tax_status", "Tax Status")
    ],
    "GAP": [
        ("dates", "Duration"),
        ("gap_justification_remarks", "Justification")
    ],
    "EQUITY": [
        ("employer", "Employer"),
        ("stock_options_value", "Stock Value"),
        ("currency", "Currency")
    ],
    "ADDITIONAL_NOTES": [
        ("notes", "Note Details")
    ]
}