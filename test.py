import pandas as pd
import numpy as np

def generate_final_summary(df):
    """
    Groups data by employer and consolidates financial totals with 
    a chronologically interwoven narrative of audit remarks.
    """
    df_copy = df.copy()
    
    # Define the group keys
    group_cols = ['Parent_employer_name', 'Subsidary_employer_name', 'Designation', 'Country']
    
    # Define column sets for processing
    income_sets = {
        'Primary': ['Primary_income_pretax', 'Primary_income_posttax', 'Primary_income_currency'],
        'Client': ['Client_declared_pretax', 'Client_declared_posttax', 'Client_declared_currency']
    }

    def process_group(group):
        # 1. Sort by Start_employment to ensure chronological remarks
        group = group.sort_values('Start_employment')
        
        res = {}
        group_remarks = []

        # 2. Financial Aggregation Logic
        for prefix, cols in income_sets.items():
            pre, post, curr = cols
            
            # Totals
            res[f'Total_{prefix}_Pretax'] = group[pre].sum()
            res[f'Total_{prefix}_Posttax'] = group[post].sum()
            
            # Annualized Averages (Normalized for months where specific income exists)
            pre_tenure = group.loc[group[pre].notnull(), 'row_tenure_months'].sum()
            res[f'Annualized_Avg_{prefix}_Pretax'] = (group[pre].sum() / pre_tenure * 12) if pre_tenure > 0 else np.nan
            
            post_tenure = group.loc[group[post].notnull(), 'row_tenure_months'].sum()
            res[f'Annualized_Avg_{prefix}_Posttax'] = (group[post].sum() / post_tenure * 12) if post_tenure > 0 else np.nan

        # 3. Interwoven Remarks Logic (Row by Row)
        for _, row in group.iterrows():
            row_notes = []
            
            # Order: Primary Inflation -> Client Inflation -> Primary Tax -> Client Tax
            remark_targets = [
                'Primary_Inflation_Remarks', 
                'Client_Inflation_Remarks',
                'Primary_Tax_Inference_Remarks', 
                'Client_Tax_Inference_Remarks'
            ]
            
            for col in remark_targets:
                if col in row and pd.notnull(row[col]):
                    row_notes.append(str(row[col]))
            
            if row_notes:
                group_remarks.append("\n".join(row_notes))

        # Combine all row remarks into one block for the group
        res['rm_assist_remarks'] = "\n\n".join(group_remarks)
        return pd.Series(res)

    # Execute GroupBy
    final_summary = df_copy.groupby(group_cols, observed=True).apply(process_group).reset_index()
    
    return final_summary
