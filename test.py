import pandas as pd
import numpy as np

def generate_final_summary(df):
    """
    Groups data by employer and consolidates financial totals, date ranges, 
    and narrative audit trails including a mathematical breakdown of annualized averages.
    """
    df_copy = df.copy()
    group_cols = ['Parent_employer_name', 'Subsidary_employer_name', 'Designation', 'Country']
    
    income_sets = {
        'Primary': ['Primary_income_pretax', 'Primary_Flag', 'Primary_income_currency'],
        'Client': ['Client_declared_pretax', 'Client_Flag', 'Client_declared_currency']
    }

    def process_group(group):
        # Internal Date Conversion
        s_dates = pd.to_datetime(group['Start_employment'], errors='coerce')
        e_dates = pd.to_datetime(group['End_employment'], errors='coerce')
        group = group.sort_values('Start_employment')
        
        res = {}
        res['Employment_Start'] = s_dates.min().strftime('%m-%Y') if s_dates.min() else None
        res['Employment_End'] = e_dates.max().strftime('%m-%Y') if e_dates.max() else None
        res['Total_Tenure_Months'] = group['row_tenure_months'].sum()

        # Narrative Setup
        parent, sub = group['Parent_employer_name'].iloc[0], group['Subsidary_employer_name'].iloc[0]
        group_remarks = [f"### EMPLOYMENT RECORD: {parent} ({sub})", f"**Overall Tenure:** {res['Employment_Start']} to {res['Employment_End']} ({res['Total_Tenure_Months']} months)\n"]

        # Financial Aggregation & Math Audit Trail
        for prefix, cols in income_sets.items():
            pre_col, flag_col, curr_col = cols
            
            res[f'{prefix}_Currency'] = group[curr_col].dropna().iloc[0] if not group[curr_col].dropna().empty else "N/A"
            currency = res[f'{prefix}_Currency']
            
            # 1. Standard Totals
            total_pretax = group[pre_col].sum()
            res[f'Total_{prefix}_Pretax'] = total_pretax
            
            # 2. Build the "Mathematical Receipt" for Annualized Average
            calculation_steps = []
            valid_tenure = group.loc[group[pre_col].notnull(), 'row_tenure_months'].sum()
            
            for _, row in group.iterrows():
                if pd.notnull(row[pre_col]):
                    label = "Documented income" if row[flag_col] == "Present" else "Inflation/Tax adjusted income"
                    year_label = f"{row['Start_employment']} to {row['End_employment']}"
                    calculation_steps.append(f"{label} {currency} {row[pre_col]:,.2f} for tenure {year_label}")

            # Construct the final audit string for this specific income set
            if calculation_steps and valid_tenure > 0:
                annualized_val = (total_pretax / valid_tenure) * 12
                res[f'Annualized_Avg_{prefix}_Pretax'] = annualized_val
                
                math_string = "Total income during tenure = " + " + ".join(calculation_steps)
                math_string += f"\n\nAnnualized average income is ({total_pretax:,.2f} / {valid_tenure} months) x 12 = {currency} {annualized_val:,.2f}"
                res[f'{prefix}_Annualized_Audit_Trail'] = math_string
            else:
                res[f'Annualized_Avg_{prefix}_Pretax'] = np.nan
                res[f'{prefix}_Annualized_Audit_Trail'] = "No valid data to calculate average."

        # 3. Narrative Remarks (Chronological)
        for _, row in group.iterrows():
            row_notes = [str(row[c]) for c in ['Primary_Inflation_Remarks', 'Client_Inflation_Remarks', 'Primary_Tax_Inference_Remarks', 'Client_Tax_Inference_Remarks'] if c in row and pd.notnull(row[c])]
            if row_notes:
                group_remarks.append(f"#### Tenure Segment: {row['Start_employment']} to {row['End_employment']}\n" + "\n".join(row_notes) + "\n---")

        res['rm_assist_remarks'] = "\n".join(group_remarks)
        return pd.Series(res)

    final_summary = df_copy.groupby(group_cols, observed=True).apply(process_group).reset_index()
    return final_summary
