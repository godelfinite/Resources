def generate_inflation_remarks(df, pre_col, post_col, curr_col, meta_prefix):
    df_copy = df.copy()
    
    # Metadata map
    m_factor = f'{meta_prefix}_Inflation_Factor'
    m_period = f'{meta_prefix}_Ref_Time_Period'
    m_ref_months = f'{meta_prefix}_Ref_Period_months'
    m_ref_amount = f'{meta_prefix}_Ref_Amount'
    m_direction = f'{meta_prefix}_Adjustment_Direction'
    m_remark_col = f'{meta_prefix}_Inflation_Remarks'
    
    def construct_template(row):
        if pd.isna(row[m_ref_amount]) or pd.isna(row[m_factor]):
            return np.nan
        
        tax_type = "pre-tax" if pd.notnull(row[pre_col]) else "post-tax"
        final_val = row[pre_col] if tax_type == "pre-tax" else row[post_col]
        currency = row[curr_col]
        
        ref_monthly = row[m_ref_amount] / row[m_ref_months]
        
        # Handle logic based on direction
        if row[m_direction] == 'deflated':
            op_symbol, op_word = "/", "divided"
            adj_monthly = ref_monthly / row[m_factor]
        else:
            op_symbol, op_word = "x", "multiplied"
            adj_monthly = ref_monthly * row[m_factor]
        
        template = (
            f"* The inferred {tax_type} income for the tenure spanning {row['Start_employment']} to {row['End_employment']} "
            f"({row['row_tenure_months']} months) is {currency} {final_val:,.2f}\n"
            f"* This figure is derived using reference {tax_type} income of {currency} {row[m_ref_amount]:,.2f} "
            f"from the period {row[m_period]} tenure ({row[m_ref_months]} months) and adjusted for inflation.\n"
            f"* Monthly income for the reference tenure is calculated as {currency} {row[m_ref_amount]:,.2f} / "
            f"{row[m_ref_months]} = {currency} {ref_monthly:,.2f}\n"
            f"* The reference monthly income is adjusted for inflation using the country-specific inflation index of "
            f"{row['Country']} ({row[m_factor]:.3f}) as {currency} {ref_monthly:,.2f} {op_symbol} {row[m_factor]:.3f} = "
            f"{currency} {adj_monthly:,.2f}.\n"
            f"* Extrapolating this adjusted monthly income over the {row['row_tenure_months']}-month tenure from "
            f"{row['Start_employment']} to {row['End_employment']} yields the final inferred {tax_type} income of "
            f"{currency} {adj_monthly:,.2f} x {row['row_tenure_months']} months = {currency} {final_val:,.2f}"
        )
        return template

    df_copy[m_remark_col] = df_copy.apply(construct_template, axis=1)
    return df_copy
