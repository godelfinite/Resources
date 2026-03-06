import json
import os
import webbrowser

# Import the configuration from config.py

from config import TABLE_CONFIG


INPUT_FILE = 'data.json'
OUTPUT_FILE = 'placards.html'

TEMPLATE = r"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Candidate Analysis Dashboard</title>
    <style>
        :root {
            --text-main: #0f172a; --text-sub: #64748b; --border: #cbd5e1; --bg: #f8fafc;
            --emp: #2563eb; --equity: #8b5cf6; --gap: #475569; --notes: #0ea5e9;
        }

        body { font-family: 'Inter', system-ui, sans-serif; background: var(--bg); color: var(--text-main); padding: 20px; margin: 0; line-height: 1.6; }
        .container { width: 96%; max-width: 1800px; margin: 0 auto; }
        .header-main { margin-bottom: 25px; border-bottom: 2px solid var(--border); padding-bottom: 15px; }
        .header-main h1 { margin: 0; font-size: 2rem; font-weight: 800; }
        
        h2.section-title { margin: 40px 0 15px; font-size: 1rem; text-transform: uppercase; letter-spacing: 1.5px; color: var(--text-sub); border-bottom: 2px solid var(--border); padding-bottom: 10px; }
        
        .summary-content { background: white; border: 1px solid var(--border); padding: 25px; border-radius: 12px; margin-bottom: 25px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }

        .placard { background: white; border: 1px solid var(--border); border-radius: 12px; margin-bottom: 20px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }
        .p-header { padding: 20px 28px; cursor: pointer; display: flex; justify-content: space-between; align-items: center; }
        
        .type-EMPLOYMENT { border-left: 10px solid var(--emp); }
        .type-EQUITY_COMPENSATION { border-left: 10px solid var(--equity); }
        .type-GAP { border-left: 10px solid var(--gap); }
        .type-ADDITIONAL_NOTES { border-left: 10px solid var(--notes); }

        .header-titles { display: flex; flex-direction: column; }
        .parent-name { font-weight: 900; font-size: 1.25rem; }
        .type-label { font-size: 0.75rem; font-weight: 700; text-transform: uppercase; color: var(--text-sub); margin-top: 2px; letter-spacing: 0.5px; }

        .p-content { padding: 0 28px 28px; border-top: 1px solid #f1f5f9; }
        .hidden { display: none; }
        .role-title { font-weight: 700; color: var(--text-main); font-size: 1.15rem; margin: 25px 0 12px 0; display: block; border-left: 4px solid #e2e8f0; padding-left: 12px; }

        .sub-toggle { 
            display: flex; justify-content: space-between; align-items: center; 
            padding: 12px 16px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; 
            cursor: pointer; font-size: 0.8rem; font-weight: 800; margin-top: 18px; color: var(--text-sub);
        }
        .chevron { transition: transform 0.3s ease; font-size: 0.85rem; }
        .expanded > .p-header .chevron, .expanded > .sub-toggle .chevron { transform: rotate(180deg); }

        blockquote { margin: 12px 0 0 0; padding: 18px 24px; border-left: 6px solid; border-radius: 0 10px 10px 0; font-size: 0.98rem; outline: none; }
        .resp-quote { border-color: #22c55e; background: #f0fdf4; color: #14532d; }
        .obs-quote { border-color: #f59e0b; background: #fffbeb; color: #78350f; }
        .qc-quote { border-color: #be123c; background: #fff1f2; color: #881337; }

        .source-tag { display: inline-block; background: #f1f5f9; color: #475569; font-size: 0.8rem; padding: 4px 10px; border-radius: 6px; margin: 5px 6px 0 0; border: 1px solid #cbd5e1; font-weight: 500; }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        td { padding: 14px 0; border-bottom: 1px solid #f1f5f9; font-size: 1rem; }
        .label { color: var(--text-sub); width: 40%; font-weight: 600; }
        
        .btn-edit { float: right; margin-top: 25px; font-size: 0.85rem; padding: 8px 18px; cursor: pointer; background: #fff; border: 1px solid var(--border); border-radius: 8px; font-weight: 700; }
        input { width: 100%; border: 1px solid transparent; background: transparent; font-size: inherit; font-family: inherit; color: inherit; outline: none; }
        
        /* Edit State Highlight */
        .editable { 
            border: 1px solid var(--border) !important; 
            background: #fff !important; 
            border-radius: 4px; 
            padding: 4px 8px !important; 
        }
        blockquote.editable { border: 1px solid var(--border); border-left: 6px solid; }
    </style>
</head>
<body>
<div class="container">
    <div class="header-main">
        <h1 id="c-name"></h1><p id="c-meta"></p>
    </div>
    <h2 class="section-title">Employment Summary</h2>
    <div class="summary-content" id="summary"></div>
    <h2 class="section-title">Employment History</h2>
    <div id="timeline-container"></div>
    <h2 class="section-title">Additional Notes</h2>
    <div id="notes-container"></div>
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
        document.getElementById('summary').innerText = data.employment_summary || "";
        
        const timeline = document.getElementById('timeline-container');
        const notesCont = document.getElementById('notes-container');
        let gapCounter = 0;

        data.timeline_entries.forEach(e => {
            let rows = "";
            const currentType = e.entry_type;
            const fields = config[currentType] || [];
            
            fields.forEach(([key, label]) => {
                const val = getNested(e, key);
                rows += `<tr><td class="label">${label}</td><td><input type="text" value="${val || ''}" disabled></td></tr>`;
            });

            const docs = e.source_documents || e.source_attribution || [];
            if(docs.length > 0) {
                let docHtml = docs.map(d => `<span class="source-tag">📄 ${d}</span>`).join('');
                rows += `<tr><td class="label">Source Attribution</td><td>${docHtml}</td></tr>`;
            }

            let hTitle = e.parent_company || e.employer;
            if (currentType === "GAP") hTitle = `GAP PERIOD ${++gapCounter}`;

            timeline.innerHTML += `
                <div class="placard type-${currentType}">
                    <div class="p-header" onclick="toggleParent(this)">
                        <div class="header-titles">
                            <span class="parent-name">${hTitle}</span>
                            <span class="type-label">${currentType.replace('_', ' ')}</span>
                        </div>
                        <span class="chevron">▼</span>
                    </div>
                    <div class="p-content hidden">
                        <button class="btn-edit" onclick="toggleEdit(this)">Edit Values</button>
                        ${e.role ? `<span class="role-title">${e.role}</span>` : ''}
                        <table>${rows}</table>
                        ${createBlock("Responsibility", e.responsibility, "resp-quote")}
                        ${createBlock("Agent Observations", e.observations_by_agent, "obs-quote")}
                        ${createBlock("QC Assessment", e.qc_assessment, "qc-quote")}
                        ${createBlock("Client Income Attribution", e.client_declared_income?.income_attribution_remarks, "obs-quote")}
                        ${createBlock("Primary Income Attribution", e.primary_corroboration_income?.income_attribution_remarks, "obs-quote")}
                    </div>
                </div>`;
        });

        // Single object handling for Additional Notes
        if (data.additional_profile_notes) {
            const n = data.additional_profile_notes;
            const docHtml = (n.source_documents || []).map(d => `<span class="source-tag">📄 ${d}</span>`).join('');
            notesCont.innerHTML += `
                <div class="placard type-ADDITIONAL_NOTES">
                    <div class="p-header" onclick="toggleParent(this)">
                        <span class="parent-name">Additional Note</span>
                        <span class="chevron">▼</span>
                    </div>
                    <div class="p-content hidden">
                        <button class="btn-edit" onclick="toggleEdit(this)">Edit Values</button>
                        <table>
                            <tr><td class="label">Note</td><td><input type="text" value="${n.notes || ''}" disabled></td></tr>
                            <tr><td class="label">Source Attribution</td><td>${docHtml}</td></tr>
                        </table>
                    </div>
                </div>`;
        }
    }

    function createBlock(title, text, style) {
        if (!text) return "";
        return `
            <div class="sub-collapsible">
                <div class="sub-toggle" onclick="toggleSub(this)"><span>${title}</span><span class="chevron">▼</span></div>
                <blockquote class="${style} hidden" contenteditable="false">${text} </blockquote>
            </div>`;
    }

    window.toggleParent = (el) => { el.parentElement.classList.toggle('expanded'); el.nextElementSibling.classList.toggle('hidden'); };
    window.toggleSub = (el) => { el.parentElement.classList.toggle('expanded'); el.nextElementSibling.classList.toggle('hidden'); };
    
    window.toggleEdit = (btn) => {
        const content = btn.closest('.p-content');
        const inputs = content.querySelectorAll('input');
        const quotes = content.querySelectorAll('blockquote');
        const isEditing = btn.innerText === "Save Changes";
        
        inputs.forEach(i => { 
            i.disabled = isEditing; 
            i.classList.toggle('editable', !isEditing); 
        });
        quotes.forEach(q => { 
            q.contentEditable = !isEditing; 
            q.classList.toggle('editable', !isEditing);
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
    final_html = TEMPLATE.replace("{{DATA_JSON}}", json.dumps(data, indent=4)).replace("{{CONFIG}}", json.dumps(TABLE_CONFIG, indent=4))
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(final_html)
    print(f"✅ Success: {OUTPUT_FILE} created.")
    webbrowser.open('file://' + os.path.realpath(OUTPUT_FILE))

if __name__ == "__main__":
    main()
