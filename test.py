import pandas as pd
import numpy as np

def generate_final_summary(df):
    """
    Groups data by employer and consolidates financial totals, date ranges, 
    total tenure, and a professional narrative of audit remarks.
    """
    df_copy = df.copy()
    group_cols = ['Parent_employer_name', 'Subsidary_employer_name', 'Designation', 'Country']
    
    # Define column sets for income calculation
    income_sets = {
        'Primary': ['Primary_income_pretax', 'Primary_income_posttax', 'Primary_income_currency'],
        'Client': ['Client_declared_pretax', 'Client_declared_posttax', 'Client_declared_currency']
    }

    def process_group(group):
        # 1. Internal Date Conversion for accurate min/max
        s_dates = pd.to_datetime(group['Start_employment'], errors='coerce')
        e_dates = pd.to_datetime(group['End_employment'], errors='coerce')
        
        # Sort chronologically for narrative flow
        group = group.sort_values('Start_employment')
        
        res = {}
        # Min/Max dates and Total Tenure
        res['Employment_Start'] = s_dates.min().strftime('%m-%Y') if s_dates.min() else None
        res['Employment_End'] = e_dates.max().strftime('%m-%Y') if e_dates.max() else None
        res['Total_Tenure_Months'] = group['row_tenure_months'].sum()

        # Capture Currency (taking the first available, as groups share a currency)
        # We check both Primary and Client sets
        res['Group_Currency'] = (
            group['Primary_income_currency'].dropna().iloc[0] if not group['Primary_income_currency'].dropna().empty 
            else group['Client_declared_currency'].dropna().iloc[0] if not group['Client_declared_currency'].dropna().empty 
            else "N/A"
        )

        # Narrative Setup
        parent = group['Parent_employer_name'].iloc[0]
        sub = group['Subsidary_employer_name'].iloc[0]
        des = group['Designation'].iloc[0]
        country = group['Country'].iloc[0]

        group_remarks = [f"### EMPLOYMENT RECORD: {parent} ({sub})"]
        group_remarks.append(f"**Role:** {des} | **Location:** {country}")
        group_remarks.append(f"**Overall Tenure:** {res['Employment_Start']} to {res['Employment_End']} ({res['Total_Tenure_Months']} months)\n")

        # 2. Financial Aggregation
        for prefix, cols in income_sets.items():
            pre, post, curr = cols
            res[f'Total_{prefix}_Pretax'] = group[pre].sum()
            res[f'Total_{prefix}_Posttax'] = group[post].sum()
            
            # Annualized Averages (Weighted by tenure where data exists)
            pre_tenure = group.loc[group[pre].notnull(), 'row_tenure_months'].sum()
            res[f'Annualized_Avg_{prefix}_Pretax'] = (group[pre].sum() / pre_tenure * 12) if pre_tenure > 0 else np.nan
            
            post_tenure = group.loc[group[post].notnull(), 'row_tenure_months'].sum()
            res[f'Annualized_Avg_{prefix}_Posttax'] = (group[post].sum() / post_tenure * 12) if post_tenure > 0 else np.nan

        # 3. Interwoven Remarks
        for _, row in group.iterrows():
            row_notes = []
            tenure_header = f"#### Tenure Segment: {row['Start_employment']} to {row['End_employment']}"
            
            remark_targets = [
                'Primary_Inflation_Remarks', 'Client_Inflation_Remarks',
                'Primary_Tax_Inference_Remarks', 'Client_Tax_Inference_Remarks'
            ]
            
            for col in remark_targets:
                if col in row and pd.notnull(row[col]):
                    row_notes.append(str(row[col]))
            
            if row_notes:
                group_remarks.append(tenure_header)
                group_remarks.append("\n".join(row_notes))
                group_remarks.append("---")

        res['rm_assist_remarks'] = "\n".join(group_remarks)
        return pd.Series(res)

    # Execute GroupBy
    final_summary = df_copy.groupby(group_cols, observed=True).apply(process_group).reset_index()
    
    # Column Reordering for a cleaner report
    fixed_cols = group_cols + ['Employment_Start', 'Employment_End', 'Total_Tenure_Months', 'Group_Currency']
    rest_cols = [c for c in final_summary.columns if c not in fixed_cols]
    
    return final_summary[fixed_cols + rest_cols]
