import pandas as pd
import numpy as np

def generate_final_summary(df):
    """
    Groups data by employer and consolidates financial totals, date ranges, 
    and a professional structured narrative of audit remarks.
    """
    df_copy = df.copy()
    # Correcting the typo "Subsidary" to match your dataframe if needed
    group_cols = ['Parent_employer_name', 'Subsidary_employer_name', 'Designation', 'Country']
    
    income_sets = {
        'Primary': ['Primary_income_pretax', 'Primary_income_posttax'],
        'Client': ['Client_declared_pretax', 'Client_declared_posttax']
    }

    def process_group(group):
        # 1. Sort chronologically for narrative flow
        group = group.sort_values('Start_employment')
        
        # Metadata for Headers and Date Ranges
        parent = group['Parent_employer_name'].iloc[0]
        sub = group['Subsidary_employer_name'].iloc[0]
        des = group['Designation'].iloc[0]
        country = group['Country'].iloc[0]
        
        res = {}
        # Min and Max of employment dates for this specific group
        res['Employment_Start'] = group['Start_employment'].min()
        res['Employment_End'] = group['End_employment'].max()

        # Start narrative block
        group_remarks = [f"### EMPLOYMENT RECORD: {parent} ({sub})"]
        group_remarks.append(f"**Role:** {des} | **Location:** {country}")
        group_remarks.append(f"**Overall Tenure:** {res['Employment_Start']} to {res['Employment_End']}\n")

        # 2. Financial Aggregation
        for prefix, cols in income_sets.items():
            pre, post = cols
            res[f'Total_{prefix}_Pretax'] = group[pre].sum()
            res[f'Total_{prefix}_Posttax'] = group[post].sum()
            
            # Annualized Averages (Weighted by tenure months where data is present)
            pre_tenure = group.loc[group[pre].notnull(), 'row_tenure_months'].sum()
            res[f'Annualized_Avg_{prefix}_Pretax'] = (group[pre].sum() / pre_tenure * 12) if pre_tenure > 0 else np.nan
            
            post_tenure = group.loc[group[post].notnull(), 'row_tenure_months'].sum()
            res[f'Annualized_Avg_{prefix}_Posttax'] = (group[post].sum() / post_tenure * 12) if post_tenure > 0 else np.nan

        # 3. Chronological Interwoven Remarks
        for _, row in group.iterrows():
            row_notes = []
            tenure_header = f"#### Tenure Segment: {row['Start_employment']} to {row['End_employment']}"
            
            # Specific sequence: Inflation remarks first, then Tax Inference remarks
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
                group_remarks.append(tenure_header)
                group_remarks.append("\n".join(row_notes))
                group_remarks.append("---") # Separator between segments

        res['rm_assist_remarks'] = "\n".join(group_remarks)
        return pd.Series(res)

    # Execute GroupBy
    final_summary = df_copy.groupby(group_cols, observed=True).apply(process_group).reset_index()
    
    # Reordering columns for better readability
    cols_to_order = group_cols + ['Employment_Start', 'Employment_End']
    other_cols = [c for c in final_summary.columns if c not in cols_to_order]
    
    return final_summary[cols_to_order + other_cols]
