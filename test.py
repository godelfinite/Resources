def generate_tax_inference_remarks(df, pre_col, post_col, curr_col, meta_prefix):
    """
    Generates succinct audit remarks for both Pre-tax (Gross-up) 
    and Post-tax (Net-down) inferences.
    """
    df_copy = df.copy()
    
    # Pre-tax Inference Metadata (Gross-up)
    m_pre_rate = f'{meta_prefix}_Tax_Rate'
    m_pre_url = f'{meta_prefix}_Tax_URL'
    m_pre_desc = f'{meta_prefix}_Tax_Source_Desc'
    
    # Post-tax Inference Metadata (Net-down)
    m_post_rate = f'{meta_prefix}_PostTax_Rate'
    m_post_url = f'{meta_prefix}_PostTax_URL'
    m_post_desc = f'{meta_prefix}_PostTax_Source_Desc'
    
    remark_col = f'{meta_prefix}_Tax_Inference_Remarks'

    def construct_statement(row):
        currency = row[curr_col]
        
        # Scenario 1: Pre-tax was inferred from Post-tax
        if pd.notnull(row.get(m_pre_rate)):
            rate = row[m_pre_rate] * 100
            source = row[m_pre_desc]
            url = row[m_pre_url]
            return (f"Income during tenure was reported as {currency} {row[post_col]:,.2f} (post-tax) "
                    f"which is converted to its pre-tax equivalent ({currency} {row[pre_col]:,.2f}) "
                    f"applying a {rate:.2f}% tax rate sourced from {source} ({url}).")

        # Scenario 2: Post-tax was inferred from Pre-tax
        elif pd.notnull(row.get(m_post_rate)):
            rate = row[m_post_rate] * 100
            source = row[m_post_desc]
            url = row[m_post_url]
            return (f"Income during tenure was reported as {currency} {row[pre_col]:,.2f} (pre-tax) "
                    f"which is converted to its post-tax equivalent ({currency} {row[post_col]:,.2f}) "
                    f"applying a {rate:.2f}% tax rate sourced from {source} ({url}).")
        
        return np.nan

    df_copy[remark_col] = df_copy.apply(construct_statement, axis=1)
    return df_copy
