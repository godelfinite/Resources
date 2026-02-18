import pandas as pd
import numpy as np

def generate_final_summary(df):
    """
    Groups data by employer and consolidates financial totals, date ranges, 
    tenure, currencies, and a professional narrative, adding a mathematical 
    audit trail for annualized averages.
    """
    df_copy = df.copy()
    group_cols = ['Parent_employer_name', 'Subsidary_employer_name', 'Designation', 'Country']
    
    income_sets = {
        'Primary': ['Primary_income_pretax', 'Primary_income_posttax', 'Primary_income_currency', 'Primary_Flag'],
        'Client': ['Client_declared_pretax', 'Client_declared_posttax', 'Client_declared_currency', 'Client_Flag']
    }

    def process_group(group):
        # 1. Internal Date Conversion for accurate min/max
        s_dates = pd.to_datetime(group['Start_employment'], errors='coerce')
        e_dates = pd.to_datetime(group['End_employment'], errors='coerce')
        
        # Sort chronologically for narrative and math flow
        group = group.sort_values('Start_employment')
        
        res = {}
        # Date & Tenure logic
        res['Employment_Start'] = s_dates.min().strftime('%m-%Y') if s_dates.min() else None
        res['Employment_End'] = e_dates.max().strftime('%m-%Y') if e_dates.max() else None
        res['Total_Tenure_Months'] = group['row_tenure_months'].sum()

        # Narrative Header Setup
        parent = group['Parent_employer_name'].iloc[0]
        sub = group['Subsidary_employer_name'].iloc[0]
        des = group['Designation'].iloc[0]
        country = group['Country'].iloc[0]
        group_remarks = [f"### EMPLOYMENT RECORD: {parent} ({sub})", 
                         f"**Role:** {des} | **Location:** {country}",
                         f"**Overall Tenure:** {res['Employment_Start']} to {res['Employment_End']} ({res['Total_Tenure_Months']} months)\n"]

        # 2. Financial Aggregation & Math Audit Trail Generation
        for prefix, cols in income_sets.items():
            pre, post, curr, flag = cols
            
            # Currency Capture
            res[f'{prefix}_Currency'] = group[curr].dropna().iloc[0] if not group[curr].dropna().empty else "N/A"
            currency = res[f'{prefix}_Currency']
            
            # Financial Totals
            res[f'Total_{prefix}_Pretax'] = group[pre].sum()
            res[f'Total_{prefix}_Posttax'] = group[post].sum()
            
            # Annualized Average Calculation
            pre_tenure_sum = group.loc[group[pre].notnull(), 'row_tenure_months'].sum()
            if pre_tenure_sum > 0:
                avg_val = (res[f'Total_{prefix}_Pretax'] / pre_tenure_sum) * 12
                res[f'Annualized_Avg_{prefix}_Pretax'] = avg_val
                
                # --- NEW MATH AUDIT TRAIL LOGIC ---
                calc_steps = []
                for _, row in group.iterrows():
                    if pd.notnull(row[pre]):
                        label = "Documented income" if row[flag] == "Present" else "Inflation/Tax adjusted income"
                        calc_steps.append(f"{label} {currency} {row[pre]:,.2f} for tenure {row['Start_employment']} to {row['End_employment']}")
                
                math_string = "Total income during tenure = " + " + ".join(calc_steps)
                math_string += f"\n\nAnnualized average income is ({res[f'Total_{prefix}_Pretax']:,.2f} / {pre_tenure_sum} months) x 12 = {currency} {avg_val:,.2f}"
                res[f'{prefix}_Annualized_Audit_Trail'] = math_string
            else:
                res[f'Annualized_Avg_{prefix}_Pretax'] = np.nan
                res[f'{prefix}_Annualized_Audit_Trail'] = "No valid data to calculate."

            # Post-tax Annualized Avg (standard calculation)
            post_tenure_sum = group.loc[group[post].notnull(), 'row_tenure_months'].sum()
            res[f'Annualized_Avg_{prefix}_Posttax'] = (res[f'Total_{prefix}_Posttax'] / post_tenure_sum * 12) if post_tenure_sum > 0 else np.nan

        # 3. Interwoven Narrative Remarks
        for _, row in group.iterrows():
            row_notes = []
            remark_cols = ['Primary_Inflation_Remarks', 'Client_Inflation_Remarks', 'Primary_Tax_Inference_Remarks', 'Client_Tax_Inference_Remarks']
            for col in remark_cols:
                if col in row and pd.notnull(row[col]):
                    row_notes.append(str(row[col]))
            
            if row_notes:
                group_remarks.append(f"#### Tenure Segment: {row['Start_employment']} to {row['End_employment']}")
                group_remarks.append("\n".join(row_notes))
                group_remarks.append("---")

        res['rm_assist_remarks'] = "\n".join(group_remarks)
        return pd.Series(res)

    # 4. Final Processing & Column Ordering
    final_summary = df_copy.groupby(group_cols, observed=True).apply(process_group).reset_index()
    
    # Organising columns logically
    ordered_cols = group_cols + ['Employment_Start', 'Employment_End', 'Total_Tenure_Months']
    p_cols = ['Primary_Currency', 'Total_Primary_Pretax', 'Annualized_Avg_Primary_Pretax', 'Primary_Annualized_Audit_Trail']
    c_cols = ['Client_Currency', 'Total_Client_Pretax', 'Annualized_Avg_Client_Pretax', 'Client_Annualized_Audit_Trail']
    
    return final_summary[ordered_cols + p_cols + c_cols + ['rm_assist_remarks']]
