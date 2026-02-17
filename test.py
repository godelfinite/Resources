def impute_income_group(df, pre_col, post_col, curr_col, meta_prefix):
    """
    Imputes income by looping through groups explicitly to maintain column accessibility.
    """
    df_copy = df.copy()
    group_cols = ['Parent_employer_name', 'Subsidiary_employer_name', 'Designation', 'Country']
    
    # Initialize metadata columns
    meta_cols = {
        'factor': f'{meta_prefix}_Inflation_Factor',
        'period': f'{meta_prefix}_Ref_Time_Period'
    }
    for col in meta_cols.values():
        df_copy[col] = np.nan

    # Identify unique groups
    unique_groups = df_copy[group_cols].drop_duplicates()
    processed_frames = []

    for _, row_group in unique_groups.iterrows():
        # Filter the dataframe for the specific group
        mask = True
        for col in group_cols:
            mask &= (df_copy[col] == row_group[col])
        
        group = df_copy[mask].copy().sort_values('Start_employment')
        indices = group.index.tolist()
        current_country = row_group['Country']

        def is_missing(idx):
            return pd.isnull(group.loc[idx, pre_col]) and pd.isnull(group.loc[idx, post_col])

        # --- Backward Pass (Deflation) ---
        for i in range(len(indices) - 2, -1, -1):
            curr_idx, next_idx = indices[i], indices[i+1]
            if is_missing(curr_idx):
                ref_pre, ref_post = group.loc[next_idx, pre_col], group.loc[next_idx, post_col]
                if pd.notnull(ref_pre) or pd.notnull(ref_post):
                    use_pre = pd.notnull(ref_pre)
                    ref_val = ref_pre if use_pre else ref_post
                    
                    ref_yr = group.loc[next_idx, 'End_employment'][-4:]
                    curr_yr = group.loc[curr_idx, 'End_employment'][-4:]
                    factor = get_inflation_factor(curr_yr, ref_yr, current_country)
                    
                    imputed_val = (ref_val / group.loc[next_idx, 'row_tenure_months']) / factor * group.loc[curr_idx, 'row_tenure_months']
                    
                    group.at[curr_idx, pre_col if use_pre else post_col] = imputed_val
                    group.at[curr_idx, curr_col] = group.loc[next_idx, curr_col]
                    group.at[curr_idx, meta_cols['factor']] = factor
                    group.at[curr_idx, meta_cols['period']] = f"{group.loc[next_idx, 'Start_employment']}-{group.loc[next_idx, 'End_employment']}"

        # --- Forward Pass (Inflation) ---
        for i in range(1, len(indices)):
            curr_idx, prev_idx = indices[i], indices[i-1]
            if is_missing(curr_idx):
                ref_pre, ref_post = group.loc[prev_idx, pre_col], group.loc[prev_idx, post_col]
                if pd.notnull(ref_pre) or pd.notnull(ref_post):
                    use_pre = pd.notnull(ref_pre)
                    ref_val = ref_pre if use_pre else ref_post
                    
                    ref_yr = group.loc[prev_idx, 'End_employment'][-4:]
                    curr_yr = group.loc[curr_idx, 'End_employment'][-4:]
                    factor = get_inflation_factor(ref_yr, curr_yr, current_country)
                    
                    imputed_val = (ref_val / group.loc[prev_idx, 'row_tenure_months']) * factor * group.loc[curr_idx, 'row_tenure_months']
                    
                    group.at[curr_idx, pre_col if use_pre else post_col] = imputed_val
                    group.at[curr_idx, curr_col] = group.loc[prev_idx, curr_col]
                    group.at[curr_idx, meta_cols['factor']] = factor
                    group.at[curr_idx, meta_cols['period']] = f"{group.loc[prev_idx, 'Start_employment']}-{group.loc[prev_idx, 'End_employment']}"
        
        processed_frames.append(group)

    # Recombine all processed groups
    return pd.concat(processed_frames).sort_index()
