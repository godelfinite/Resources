import time
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
import numpy as np

def infer_pretax_income_batched(df, pre_col, post_col, meta_prefix, batch_size=30, min_window=75):
    df_copy = df.copy()
    
    # Metadata column setup
    meta_map = {
        'paid': f'{meta_prefix}_Tax_Paid',
        'rate': f'{meta_prefix}_Tax_Rate',
        'url': f'{meta_prefix}_Tax_URL',
        'desc': f'{meta_prefix}_Tax_Source_Desc'
    }
    
    for col in meta_map.values():
        if col not in df_copy.columns:
            df_copy[col] = np.nan

    # Filter for rows that actually need processing
    target_indices = df_copy[df_copy[pre_col].isnull() & df_copy[post_col].notnull()].index.tolist()
    
    if not target_indices:
        return df_copy

    print(f"Processing {len(target_indices)} rows in optimized batches of {batch_size}...")

    for i in range(0, len(target_indices), batch_size):
        # 1. Start the clock for this batch
        batch_start_time = time.time()
        
        current_batch_indices = target_indices[i:i + batch_size]
        
        # 2. Fire the parallel requests
        with ThreadPoolExecutor(max_workers=batch_size) as executor:
            future_to_index = {
                executor.submit(pretax_from_posttax, df_copy.loc[idx, post_col]): idx 
                for idx in current_batch_indices
            }
            
            for future in future_to_index:
                idx = future_to_index[future]
                try:
                    tax_results = future.result()
                    df_copy.at[idx, pre_col] = tax_results.get("estimated_pre_tax_compensation")
                    df_copy.at[idx, meta_map['paid']] = tax_results.get("estimaed_tax_paid")
                    df_copy.at[idx, meta_map['rate']] = tax_results.get("tax_rate")
                    df_copy.at[idx, meta_map['desc']] = tax_results.get("source_description")
                    df_copy.at[idx, meta_map['url']] = tax_results.get("source_url")
                except Exception as e:
                    print(f"Error at index {idx}: {e}")

        # 3. Time-Drift Calculation
        elapsed_time = time.time() - batch_start_time
        
        # If we have more batches to go, check the window
        if i + batch_size < len(target_indices):
            if elapsed_time < min_window:
                wait_time = min_window - elapsed_time
                print(f"Batch processed in {elapsed_time:.2f}s. Waiting {wait_time:.2f}s for the next window...")
                time.sleep(wait_time)
            else:
                print(f"Batch took {elapsed_time:.2f}s (exceeding window). Firing next batch immediately.")

    return df_copy
