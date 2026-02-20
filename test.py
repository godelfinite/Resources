import pandas as pd

def generate_qc_remarks(row):
    # --- 1. Header Construction ---
    header = f"🏢 {row['employer_name']} | 📋 {row['designation']} | 📍 {row['country']}\n"
    
    # Extract values
    declared = row['client_declared_income']
    primary = row['primary_corroborated_income']
    secondary = row['secondary_corroborated_income']
    
    warnings = []
    comparison_status = ""

    # --- 2. Validation Checks ---
    # Check Declared Income
    if pd.isna(declared) or declared <= 0:
        warnings.append("⚠️ WARNING: Client declared income is MISSING. RM, please fill this up ASAP!")
    
    # Check Corroboration Availability
    if pd.isna(primary) and pd.isna(secondary):
        warnings.append("🚨 WARNING: Both primary & secondary corroboration are missing. RM, please trigger benchmarking.")
    
    # --- 3. Comparison Logic ---
    # We only compare if we have Declared Income AND at least one corroboration
    if pd.notna(declared) and (pd.notna(primary) or pd.notna(secondary)):
        # Determine which source to use (Priority: Primary > Secondary)
        source_val = primary if pd.notna(primary) else secondary
        source_label = "Primary" if pd.notna(primary) else "Secondary"
        
        # Calculate Variance
        variance = ((declared - source_val) / source_val) * 100
        
        # Threshold Check (Example: 10%)
        if variance <= 10:
            comparison_status = f"✅ Client declared income exceeds {source_label} by {variance:.2f}%, which is within acceptable range."
        else:
            comparison_status = f"🚩 WARNING: Client declared income exceeds {source_label} by {variance:.2f}%. This is OUTSIDE range! RM justification required."
    
    # Combine everything
    # Join warnings with a newline, then add comparison status if it exists
    full_remark = header + "\n".join(warnings)
    if comparison_status:
        full_remark += f"\n{comparison_status}"
        
    return full_remark

# Application:
# df['qc_agent_remarks'] = df.apply(generate_qc_remarks, axis=1)
