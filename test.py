def infer_posttax_income_batched(df, pre_col, post_col, curr_col, meta_prefix, batch_size=30, min_window=75):
    """
    Fills missing post-tax values ONLY if the group has partial post-tax data.
    Captures full metadata: Tax Paid, Rate, Source, and URL.
    """
    df_copy = df.copy()
    group_cols = ['Parent_employer_name', 'Subsidary_employer_name', 'Designation', 'Country']
    
    # Mirroring the metadata fields from the pre-tax function
    meta_map = {
        'paid': f'{meta_prefix}_Tax_Paid',
        'rate': f'{meta_prefix}_Tax_Rate',
        'url': f'{meta_prefix}_Tax_URL',
        'desc': f'{meta_prefix}_Tax_Source_Desc'
    }
    
    for col in meta_map.values():
        if col not in df_copy.columns:
            df_copy[col] = np.nan

    # 1. Targeted Group Check: Only fill gaps in groups that already have some post-tax data
    group_presence = df_copy.groupby(group_cols)[post_col].transform(lambda x: x.notnull().any())
    
    # 2. Identify indices: (In a partial group) AND (Post-tax is NaN) AND (Pre-tax is present)
    target_indices = df_copy[
        (group_presence == True) & 
        (df_copy[post_col].isnull()) & 
        (df_copy[pre_col].notnull())
    ].index.tolist()
    
    if not target_indices:
        print(f"No partial post-tax gaps found for {meta_prefix}.")
        return df_copy

    print(f"Filling {len(target_indices)} post-tax gaps for {meta_prefix} using Gemini...")

    for i in range(0, len(target_indices), batch_size):
        batch_start_time = time.time()
        current_batch_indices = target_indices[i:i + batch_size]
        
        def worker(idx):
            row = df_copy.loc[idx]
            query = {
                "claim_id": f"row_{idx}_net_infer",
                "country": row['Country'],
                "currency": row[curr_col],
                "claimed_pre-tax_annual_compensation": row[pre_col]
            }
            # Calling your specific Gemini function for net income
            return posttax_from_pretax(query)

        with ThreadPoolExecutor(max_workers=batch_size) as executor:
            future_to_index = {executor.submit(worker, idx): idx for idx in current_batch_indices}
            
            for future in future_to_index:
                idx = future_to_index[future]
                try:
                    response = future.result()
                    # Mapping identical fields to the Pre-Tax results
                    df_copy.at[idx, post_col] = response.get("estimated_post_tax_compensation")
                    df_copy.at[idx, meta_map['paid']] = response.get("estimaed_tax_paid")
                    df_copy.at[idx, meta_map['rate']] = response.get("tax_rate")
                    df_copy.at[idx, meta_map['desc']] = response.get("source_description")
                    df_copy.at[idx, meta_map['url']] = response.get("source_url")
                except Exception as e:
                    print(f"Gemini Error at index {idx}: {e}")

        # Rate Limit Drift Logic
        elapsed_time = time.time() - batch_start_time
        if i + batch_size < len(target_indices):
            wait_time = max(0, min_window - elapsed_time)
            if wait_time > 0:
                time.sleep(wait_time)

    return df_copy
