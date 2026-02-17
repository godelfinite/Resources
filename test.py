def infer_posttax_income_batched(df, pre_col, post_col, curr_col, meta_prefix, batch_size=30, min_window=75):
    """
    Fills missing post-tax values ONLY if the group already contains some post-tax data.
    Ensures group-level aggregation is not misleading.
    """
    df_copy = df.copy()
    group_cols = ['Parent_employer_name', 'Subsidary_employer_name', 'Designation', 'Country']
    
    # 1. Identify Groups that have 'Partial' Post-Tax data
    # We want groups where (Count of non-null Post-Tax) > 0 
    # AND (Count of null Post-Tax) > 0
    group_stats = df_copy.groupby(group_cols)[post_col].agg(['count', lambda x: x.isnull().sum()])
    group_stats.columns = ['present_count', 'missing_count']
    
    # Filter for groups that are "Partially Present"
    partial_groups = group_stats[(group_stats['present_count'] > 0) & (group_stats['missing_count'] > 0)].index
    
    # 2. Identify specific indices to process
    # Condition: Row belongs to a partial group AND the row's post_col is actually the missing one
    target_indices = []
    if not partial_groups.empty:
        # Create a temporary key to match against partial_groups index
        temp_df = df_copy.set_index(group_cols)
        target_indices = temp_df[(temp_df.index.isin(partial_groups)) & (temp_df[post_col].isnull())].reset_index()['index'].tolist()
        # Note: If the above indexing is complex, a simple merge or loop works too:
        target_indices = df_copy[
            (df_copy.set_index(group_cols).index.isin(partial_groups)) & 
            (df_copy[post_col].isnull()) & 
            (df_copy[pre_col].notnull())
        ].index.tolist()

    if not target_indices:
        print(f"No partial groups found requiring post-tax fill for {meta_prefix}.")
        return df_copy

    print(f"Found {len(target_indices)} gaps in partially-complete groups. Starting Gemini calls...")

    # 3. Optimized Batch Loop (Same as Pre-Tax)
    for i in range(0, len(target_indices), batch_size):
        batch_start_time = time.time()
        current_batch_indices = target_indices[i:i + batch_size]
        
        def worker(idx):
            row = df_copy.loc[idx]
            query = {
                "claim_id": f"row_{idx}_post",
                "country": row['Country'],
                "currency": row[curr_col],
                "claimed_pre-tax_annual_compensation": row[pre_col]
            }
            return posttax_from_pretax(query)

        with ThreadPoolExecutor(max_workers=batch_size) as executor:
            future_to_index = {executor.submit(worker, idx): idx for idx in current_batch_indices}
            
            for future in future_to_index:
                idx = future_to_index[future]
                try:
                    response = future.result()
                    df_copy.at[idx, post_col] = response.get("estimated_post_tax_compensation")
                    # Store metadata for tax calculation remarks
                    df_copy.at[idx, f'{meta_prefix}_PostTax_Calc_Rate'] = response.get("tax_rate")
                except Exception as e:
                    print(f"Error at index {idx}: {e}")

        # Rate Limit Drift Logic
        elapsed_time = time.time() - batch_start_time
        if i + batch_size < len(target_indices):
            wait_time = max(0, min_window - elapsed_time)
            if wait_time > 0:
                time.sleep(wait_time)

    return df_copy
