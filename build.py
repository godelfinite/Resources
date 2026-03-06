import json
import os
import webbrowser
from config import TABLE_CONFIG

INPUT_FILE = 'data.json'
OUTPUT_FILE = 'placards.html'

TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
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

        body { font-family: 'Inter', system-ui, sans-serif; background: var(--bg); color: var(--text-main); padding: 40px 20px; line-height: 1.6; }
        .container { max-width: 850px; margin: 0 auto; }
        
        .header-main { margin-bottom: 30px; border-bottom: 2px solid var(--border); padding-bottom: 20px; }
        .header-main h1 { margin: 0; font-size: 1.8rem; }
        
        h2.section-title { margin: 40px 0 15px; font-size: 1.1rem; text-transform: uppercase; letter-spacing: 1px; color: var(--text-sub); border-bottom: 2px solid var(--border); padding-bottom: 10px; }

        .summary-content { background: white; border: 1px solid var(--border); padding: 20px; border-radius: 12px; margin-bottom: 30px; box-shadow: 0 2px 4px rgba(0,0,0,0.02); }

        /* Placards */
        .placard { background: white; border: 1px solid var(--border); border-radius: 12px; margin-bottom: 15px; overflow: hidden; }
        .p-header { padding: 18px 24px; cursor: pointer; display: flex; justify-content: space-between; align-items: center; background: white; }
        
        /* Accents */
        .type-EMPLOYMENT { border-left: 5px solid var(--emp); }
        .type-EQUITY { border-left: 5px solid var(--equity); }
        .type-GAP { border-left: 5px solid var(--gap); }
        .type-ADDITIONAL_NOTES { border-left: 5px solid var(--notes); }

        .parent-name { font-weight: 800; font-size: 1.1rem; }
        .p-content { padding: 0 24px 24px; border-top: 1px solid #f8fafc; }
        .hidden { display: none; }

        .role-title { font-weight: 700; color: var(--text-main); font-size: 1.1rem; margin-top: 20px; display: block; }
        
        /* Blockquotes with specific space after content */
        blockquote { margin: 20px 0; padding: 15px 20px; border-left: 5px solid; border-radius: 0 8px 8px 0; font-size: 0.95rem; }
        .resp-quote { background: #f0fdf4; border-color: #22c55e; color: #14532d; }
        .obs-quote { background: #fffbeb; border-color: #f59e0b; color: #78350f; }
        blockquote strong { display: block; font-size: 0.7rem; text-transform: uppercase; margin-bottom: 6px; opacity: 0.8; }

        /* Tables */
        table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        td { padding: 12px 0; border-bottom: 1px solid #f1f5f9; font-size: 0.95rem; }
        .label { color: var(--text-sub); width: 40%; font-weight: 500; }
        
        .btn-edit { float: right; margin-top: 20px; font-size: 0.8rem; padding: 6px 14px; cursor: pointer; background: #fff; border: 1px solid var(--border); border-radius: 6px; font-weight: 600; }
        
        .chevron { transition: transform 0.2s; font-size: 0.8rem; color: var(--text-sub); }
        .expanded .chevron { transform: rotate(180deg); }

        input, textarea { width: 100%; border: 1px solid transparent; background: transparent; font-size: inherit; font-family: inherit; padding: 2px; }
        .editable { border: 1px solid var(--border) !important; background: #fff !important; border-radius: 4px; }
    </style>
</head>
<body>

<div class="container">
    <div class="header-main">
        <h1 id="c-name"></h1>
        <p id="c-meta" style="color:var(--text-sub)"></p>
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
            
            fields.forEach(([key, label]) => {
                const val = getNested(e, key);
                rows += `<tr><td class="label">${label}</td><td><input type="text" value="${val || ''}" disabled></td></tr>`;
            });

            let hTitle = e.parent_company || e.employer || (e.entry_type === "GAP" ? "GAP PERIOD" : "RM/FO Notes");
            
            const html = `
                <div class="placard type-${e.entry_type}">
                    <div class="p-header" onclick="toggle(this)">
                        <span class="parent-name" style="color:var(--${e.entry_type.toLowerCase().split('_')[0]}-accent)">${hTitle}</span>
                        <span class="chevron">▼</span>
                    </div>
                    <div class="p-content hidden">
                        <button class="btn-edit" onclick="toggleEdit(this)">Edit Values</button>
                        ${e.role ? `<span class="role-title">${e.role}</span>` : ''}
                        <table>${rows}</table>
                        ${e.responsibilities ? `<blockquote class="resp-quote"><strong>Responsibilities</strong>${e.responsibilities} </blockquote>` : ''}
                        ${e.observation ? `<blockquote class="obs-quote"><strong>Observations</strong>${e.observation} </blockquote>` : ''}
                    </div>
                </div>`;
            
            const container = document.getElementById('cont-' + e.entry_type);
            if (container) {
                container.innerHTML += html;
                document.getElementById('sec-' + e.entry_type).classList.remove('hidden');
            }
        });
    }

    window.toggle = (el) => {
        el.parentElement.classList.toggle('expanded');
        el.nextElementSibling.classList.toggle('hidden');
    };

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
        print(f"Error: {INPUT_FILE} not found.")
        return
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Inject data and config
    final_html = TEMPLATE.replace("{{DATA_JSON}}", json.dumps(data, indent=4))
    final_html = final_html.replace("{{CONFIG}}", json.dumps(TABLE_CONFIG, indent=4))

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(final_html)
    
    webbrowser.open('file://' + os.path.realpath(OUTPUT_FILE))

if __name__ == "__main__":
    main()