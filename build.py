import json
import os
import webbrowser

# Import the configuration from config.py
try:
    from config import TABLE_CONFIG
except ImportError:
    # Fallback if config.py is missing during testing
    TABLE_CONFIG = {
        "EMPLOYMENT": [("subsidiary", "Subsidiary"), ("country", "Country"), ("dates", "Period")],
        "GAP": [("dates", "Duration"), ("gap_justification_remarks", "Justification")],
        "EQUITY": [("employer", "Employer"), ("stock_options_value", "Stock Value")],
        "ADDITIONAL_NOTES": [("notes", "Note Details")]
    }

INPUT_FILE = 'data.json'
OUTPUT_FILE = 'placards.html'

TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Candidate Analysis Report</title>
    <style>
        :root {
            --text-main: #0f172a;
            --text-sub: #64748b;
            --border: #cbd5e1;
            --bg: #f8fafc;
            --emp: #2563eb;
            --equity: #8b5cf6;
            --gap: #475569;
            --notes: #0ea5e9;
        }

        body { font-family: 'Inter', -apple-system, sans-serif; background: var(--bg); color: var(--text-main); padding: 40px 20px; line-height: 1.6; }
        .container { max-width: 850px; margin: 0 auto; }
        
        /* Profile Header */
        .header-main { margin-bottom: 30px; border-bottom: 2px solid var(--border); padding-bottom: 20px; }
        .header-main h1 { margin: 0; font-size: 1.8rem; }
        
        h2.section-title { margin: 45px 0 15px; font-size: 1.1rem; text-transform: uppercase; letter-spacing: 1px; color: var(--text-sub); border-bottom: 2px solid var(--border); padding-bottom: 10px; }

        .summary-content { background: white; border: 1px solid var(--border); padding: 20px; border-radius: 12px; margin-bottom: 30px; box-shadow: 0 2px 4px rgba(0,0,0,0.02); }

        /* Placards */
        .placard { background: white; border: 1px solid var(--border); border-radius: 12px; margin-bottom: 15px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
        .p-header { padding: 18px 24px; cursor: pointer; display: flex; justify-content: space-between; align-items: center; background: white; }
        
        /* Accents */
        .type-EMPLOYMENT { border-left: 6px solid var(--emp); }
        .type-EQUITY { border-left: 6px solid var(--equity); }
        .type-GAP { border-left: 6px solid var(--gap); }
        .type-ADDITIONAL_NOTES { border-left: 6px solid var(--notes); }

        .parent-name { font-weight: 800; font-size: 1.15rem; }
        .p-content { padding: 0 24px 24px; border-top: 1px solid #f8fafc; }
        .hidden { display: none; }

        .role-title { font-weight: 700; color: var(--text-main); font-size: 1.1rem; margin: 20px 0 10px 0; display: block; }
        
        /* Sub-Collapsible Toggle */
        .sub-toggle { 
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
            padding: 10px 14px; 
            background: #f1f5f9; 
            border-radius: 6px; 
            cursor: pointer; 
            font-size: 0.8rem; 
            font-weight: 700; 
            text-transform: uppercase; 
            margin-top: 15px;
            color: var(--text-sub);
            border: 1px solid transparent;
        }
        .sub-toggle:hover { background: #e2e8f0; border-color: var(--border); }

        /* Chevron Animation Logic */
        .chevron { transition: transform 0.2s ease; font-size: 0.8rem; color: var(--text-sub); display: inline-block; }
        .expanded > .p-header .chevron, 
        .expanded > .sub-toggle .chevron { transform: rotate(180deg); }

        /* Blockquotes */
        blockquote { margin: 10px 0 0 0; padding: 15px 20px; border-left: 5px solid; border-radius: 0 8px 8px 0; font-size: 0.95rem; }
        .resp-quote { background: #f0fdf4; border-color: #22c55e; color: #14532d; }
        .obs-quote { background: #fffbeb; border-color: #f59e0b; color: #78350f; }

        /* Tables */
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        td { padding: 12px 0; border-bottom: 1px solid #f1f5f9; font-size: 0.95rem; }
        .label { color: var(--text-sub); width: 40%; font-weight: 500; }
        
        .btn-edit { float: right; margin-top: 20px; font-size: 0.8rem; padding: 6px 14px; cursor: pointer; background: #fff; border: 1px solid var(--border); border-radius: 6px; font-weight: 600; }
        .btn-edit:hover { background: #f8fafc; border-color: var(--text-main); }
        
        input, textarea { width: 100%; border: 1px solid transparent; background: transparent; font-size: inherit; font-family: inherit; color: inherit; outline: none; }
        .editable { border: 1px solid var(--border) !important; background: #fff !important; border-radius: 4px; padding: 4px; }
    </style>
</head>
<body>

<div class="container">
    <div class="header-main">
        <h1 id="c-name"></h1>
        <p id="c-meta"></p>
    </div>

    <h2 class="section-title">Employment Summary</h2>
    <div class="summary-content" id="summary"></div>

    <div id="sec-EMPLOYMENT" class="hidden"><h2 class="section-title">Employment History</h2><div id="cont-EMPLOYMENT"></div></div>
    <div id="sec-EQUITY" class="hidden"><h2 class="section-title">Equity / Stock / Bonuses</h2><div id="cont-EQUITY"></div></div>
    <div id="sec-GAP" class="hidden"><h2 class="section-title">Gaps</h2><div id="cont-GAP"></div></div>
    <div id="sec-ADDITIONAL_NOTES" class="hidden"><h2 class="section-title">Additional Notes</h2><div id="cont-ADDITIONAL_NOTES"></div></div>
</div>

<script>
    const data = {{DATA_JSON}};
    const config = {{CONFIG}};

    // Helper to resolve nested keys like client_declared_income.total_pretax
    function getNested(obj, path) {
        return path.split('.').reduce((o, i) => (o ? o[i] : null), obj);
    }

    function init() {
        document.getElementById('c-name').innerText = data.customer_name;
        document.getElementById('c-meta').innerText = data.timeline_span + " | " + data.total_career_duration;
        document.getElementById('summary').innerText = data.employment_summary || "No summary provided.";
        
        data.timeline_entries.forEach(e => {
            let rows = "";
            const fields = config[e.entry_type] || [];
            
            // Build table rows from config
            fields.forEach(([key, label]) => {
                const val = getNested(e, key);
                // Value shows blank if missing/null/empty, but label remains as requested
                rows += `<tr><td class="label">${label}</td><td><input type="text" value="${val || ''}" disabled></td></tr>`;
            });

            // Set Header Titles based on type
            let hTitle = e.parent_company || e.employer || (e.entry_type === "GAP" ? "GAP PERIOD" : "RM/FO Notes");
            
            const html = `
                <div class="placard type-${e.entry_type}">
                    <div class="p-header" onclick="toggleParent(this)">
                        <span class="parent-name" style="color:var(--${e.entry_type.toLowerCase().split('_')[0]}-accent)">${hTitle}</span>
                        <span class="chevron">▼</span>
                    </div>
                    <div class="p-content hidden">
                        <button class="btn-edit" onclick="toggleEdit(this)">Edit Values</button>
                        ${e.role ? `<span class="role-title">${e.role}</span>` : ''}
                        <table>${rows}</table>
                        
                        ${e.responsibilities ? `
                            <div class="sub-collapsible">
                                <div class="sub-toggle" onclick="toggleSub(this)">
                                    <span>Responsibilities</span>
                                    <span class="chevron">▼</span>
                                </div>
                                <blockquote class="resp-quote hidden">${e.responsibilities} </blockquote>
                            </div>
                        ` : ''}
                        
                        ${e.observation ? `
                            <div class="sub-collapsible">
                                <div class="sub-toggle" onclick="toggleSub(this)">
                                    <span>Observations</span>
                                    <span class="chevron">▼</span>
                                </div>
                                <blockquote class="obs-quote hidden">${e.observation} </blockquote>
                            </div>
                        ` : ''}
                    </div>
                </div>`;
            
            const container = document.getElementById('cont-' + e.entry_type);
            if (container) {
                container.innerHTML += html;
                document.getElementById('sec-' + e.entry_type).classList.remove('hidden');
            }
        });
    }

    // Toggle parent placard
    window.toggleParent = (el) => {
        const placard = el.parentElement;
        const content = el.nextElementSibling;
        placard.classList.toggle('expanded');
        content.classList.toggle('hidden');
    };

    // Toggle sub-sections (Responsibilities / Observations)
    window.toggleSub = (el) => {
        const container = el.parentElement;
        const quote = el.nextElementSibling;
        container.classList.toggle('expanded');
        quote.classList.toggle('hidden');
    };

    // Handle the Edit Values toggle
    window.toggleEdit = (btn) => {
        const content = btn.closest('.p-content');
        const inputs = content.querySelectorAll('input');
        const isEditing = btn.innerText === "Save Changes";
        inputs.forEach(i => {
            i.disabled = isEditing;
            i.classList.toggle('editable');
        });
        btn.innerText = isEditing ? "Edit Values" : "Save Changes";
    };

    init();
</script>
</body>
</html>
"""

def main():
    if not os.path.exists(INPUT_FILE):
        print(f"Error: {INPUT_FILE} not found. Please ensure your data.json is in the same folder.")
        return
        
    try:
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error parsing JSON: {e}")
        return

    # Replace placeholders with actual JSON and Config data
    final_html = TEMPLATE.replace("{{DATA_JSON}}", json.dumps(data, indent=4))
    final_html = final_html.replace("{{CONFIG}}", json.dumps(TABLE_CONFIG, indent=4))

    # Writing with UTF-8 to prevent charmap encoding errors on Windows
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(final_html)
    
    print(f"✅ Pipeline complete: '{OUTPUT_FILE}' has been generated.")
    
    # Automatically open the report in the default browser
    webbrowser.open('file://' + os.path.realpath(OUTPUT_FILE))

if __name__ == "__main__":
    main()
