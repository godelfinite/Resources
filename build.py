import json
import os
import webbrowser
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
            --text-main: #0f172a;
            --text-sub: #64748b;
            --border: #cbd5e1;
            --bg: #f8fafc;
            --emp: #2563eb;
            --equity: #8b5cf6;
            --gap: #475569;
            --notes: #0ea5e9;
        }

        body { font-family: 'Inter', system-ui, sans-serif; background: var(--bg); color: var(--text-main); padding: 20px; margin: 0; line-height: 1.6; }
        
        /* Full Width Layout */
        .container { width: 96%; max-width: 1800px; margin: 0 auto; }
        
        .header-main { margin-bottom: 25px; border-bottom: 2px solid var(--border); padding-bottom: 15px; }
        .header-main h1 { margin: 0; font-size: 2rem; font-weight: 800; letter-spacing: -1px; }
        
        h2.section-title { margin: 40px 0 15px; font-size: 1rem; text-transform: uppercase; letter-spacing: 1.5px; color: var(--text-sub); border-bottom: 2px solid var(--border); padding-bottom: 10px; }

        .summary-content { background: white; border: 1px solid var(--border); padding: 25px; border-radius: 12px; margin-bottom: 25px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }

        /* Placards */
        .placard { background: white; border: 1px solid var(--border); border-radius: 12px; margin-bottom: 20px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }
        .p-header { padding: 20px 28px; cursor: pointer; display: flex; justify-content: space-between; align-items: center; }
        
        /* Sidebar Accents */
        .type-EMPLOYMENT { border-left: 10px solid var(--emp); }
        .type-EQUITY_COMPENSATION { border-left: 10px solid var(--equity); }
        .type-GAP { border-left: 10px solid var(--gap); }
        .type-ADDITIONAL_NOTES { border-left: 10px solid var(--notes); }

        .header-titles { display: flex; flex-direction: column; }
        .parent-name { font-weight: 900; font-size: 1.25rem; }
        .accessibility-label { font-size: 0.7rem; font-weight: 700; text-transform: uppercase; color: var(--text-sub); margin-top: 4px; }

        .p-content { padding: 0 28px 28px; border-top: 1px solid #f1f5f9; }
        .hidden { display: none; }

        .role-title { font-weight: 700; color: var(--text-main); font-size: 1.15rem; margin: 25px 0 12px 0; display: block; border-left: 4px solid #e2e8f0; padding-left: 12px; }
        
        /* Toggles */
        .sub-toggle { 
            display: flex; justify-content: space-between; align-items: center; 
            padding: 12px 16px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; 
            cursor: pointer; font-size: 0.8rem; font-weight: 800; 
            text-transform: uppercase; margin-top: 18px; color: var(--text-sub);
        }

        .chevron { transition: transform 0.3s ease; font-size: 0.85rem; }
        .expanded > .p-header .chevron, .expanded > .sub-toggle .chevron { transform: rotate(180deg); }

        /* Content Blocks */
        blockquote { margin: 12px 0 0 0; padding: 18px 24px; border-left: 6px solid; border-radius: 0 10px 10px 0; font-size: 0.98rem; outline: none; }
        .resp-quote { background: #f0fdf4; border-color: #22c55e; color: #14532d; }
        .obs-quote { background: #fffbeb; border-color: #f59e0b; color: #78350f; }
        .qc-quote { background: #fff1f2; border-color: #be123c; color: #881337; }

        /* Source Tags */
        .source-tag { display: inline-block; background: #f1f5f9; color: #475569; font-size: 0.8rem; padding: 4px 10px; border-radius: 6px; margin: 5px 6px 0 0; border: 1px solid #cbd5e1; font-weight: 500; }

        /* Tables - Plain formatting preserved */
        table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        td { padding: 14px 0; border-bottom: 1px solid #f1f5f9; font-size: 1rem; }
        .label { color: var(--text-sub); width: 30%; font-weight: 600; }
        
        .btn-edit { float: right; margin-top: 25px; font-size: 0.85rem; padding: 8px 18px; cursor: pointer; background: #fff; border: 1px solid var(--border); border-radius: 8px; font-weight: 700; }
        
        /* Inputs - No Borders even when editable */
        input { width: 100%; border: none; background: transparent; font-size: inherit; font-family: inherit; color: inherit; outline: none; }
    </style>
</head>
<body>

<div class="container">
    <div class="header-main">
        <h1 id="c-name">Candidate Name</h1>
        <p id="c-meta"></p>
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
        document.getElementById('summary').innerText = data.employment_summary || "No summary provided.";
        
        const timeline = document.getElementById('timeline-container');
        const notesCont = document.getElementById('notes-container');
        let gapCounter = 0;

        data.timeline_entries.forEach(e => {
            let rows = "";
            const currentType = e.entry_type;
            const configKey = (currentType === "EQUITY_COMPENSATION") ? "EQUITY_COMPENSATION" : currentType;
            const fields = config[configKey] || [];
            
            fields.forEach(([key, label]) => {
                const val = getNested(e, key);
                rows += `<tr><td class="label">${label}</td><td><input type="text" value="${val || ''}" disabled></td></tr>`;
            });

            // Handling rm_remarks and savings_rate as standard table fields
            if(currentType === "EMPLOYMENT") {
                rows += `<tr><td class="label">RM Remarks</td><td><input type="text" value="${e.rm_remarks || ''}" disabled></td></tr>`;
                rows += `<tr><td class="label">Savings Rate</td><td><input type="text" value="${e.savings_rate || ''}" disabled></td></tr>`;
            }

            // Source Attribution
            const docs = e.source_documents || e.source_attribution || [];
            if(docs.length > 0) {
                let docHtml = docs.map(d => `<span class="source-tag">📄 ${d}</span>`).join('');
                rows += `<tr><td class="label">Source Attribution</td><td>${docHtml}</td></tr>`;
            }

            let hTitle = e.parent_company || e.employer;
            if (currentType === "GAP") {
                gapCounter++;
                hTitle = `GAP PERIOD ${gapCounter}`;
            } else if (currentType === "ADDITIONAL_NOTES") {
                hTitle = "RM/FO NOTES";
            }

            const html = `
                <div class="placard type-${currentType}">
                    <div class="p-header" onclick="toggleParent(this)">
                        <div class="header-titles">
                            <span class="parent-name" style="color:var(--${currentType.toLowerCase().split('_')[0]}-accent)">${hTitle}</span>
                            <span class="accessibility-label">${currentType.replace('_', ' ')}</span>
                        </div>
                        <span class="chevron">▼</span>
                    </div>
                    <div class="p-content hidden">
                        <button class="btn-edit" onclick="toggleEdit(this)">Edit Values</button>
                        ${e.role ? `<span class="role-title">${e.role}</span>` : ''}
                        <table>${rows}</table>
                        
                        ${e.responsibility ? `
                            <div class="sub-collapsible">
                                <div class="sub-toggle" onclick="toggleSub(this)"><span>Responsibility</span><span class="chevron">▼</span></div>
                                <blockquote class="resp-quote hidden" contenteditable="false">${e.responsibility} </blockquote>
                            </div>
                        ` : ''}
                        
                        ${e.observations_by_agent ? `
                            <div class="sub-collapsible">
                                <div class="sub-toggle" onclick="toggleSub(this)"><span>Agent Observations</span><span class="chevron">▼</span></div>
                                <blockquote class="obs-quote hidden" contenteditable="false">${e.observations_by_agent} </blockquote>
                            </div>
                        ` : ''}

                        ${e.qc_assessment ? `
                            <div class="sub-collapsible">
                                <div class="sub-toggle" onclick="toggleSub(this)"><span>QC Assessment</span><span class="chevron">▼</span></div>
                                <blockquote class="qc-quote hidden" contenteditable="false">${e.qc_assessment} </blockquote>
                            </div>
                        ` : ''}
                        
                        ${e.client_declared_income?.income_attribution_remarks ? `
                            <div class="sub-collapsible">
                                <div class="sub-toggle" onclick="toggleSub(this)"><span>Income Attribution</span><span class="chevron">▼</span></div>
                                <blockquote class="obs-quote hidden" contenteditable="false">${e.client_declared_income.income_attribution_remarks} </blockquote>
                            </div>
                        ` : ''}
                    </div>
                </div>`;
            
            timeline.innerHTML += html;
        });

        // Additional Profile Notes Section
        (data.additional_profile_notes || []).forEach(n => {
            notesCont.innerHTML += `
                <div class="placard type-ADDITIONAL_NOTES">
                    <div class="p-header" onclick="toggleParent(this)">
                        <span class="parent-name">Additional Note</span>
                        <span class="chevron">▼</span>
                    </div>
                    <div class="p-content hidden">
                        <button class="btn-edit" onclick="toggleEdit(this)">Edit Values</button>
                        <table><tr><td class="label">Note</td><td><input type="text" value="${n.notes}" disabled></td></tr></table>
                    </div>
                </div>`;
        });
    }

    window.toggleParent = (el) => { el.parentElement.classList.toggle('expanded'); el.nextElementSibling.classList.toggle('hidden'); };
    window.toggleSub = (el) => { el.parentElement.classList.toggle('expanded'); el.nextElementSibling.classList.toggle('hidden'); };
    window.toggleEdit = (btn) => {
        const content = btn.closest('.p-content');
        const inputs = content.querySelectorAll('input');
        const quotes = content.querySelectorAll('blockquote');
        const isEditing = btn.innerText === "Save Changes";
        inputs.forEach(i => { i.disabled = isEditing; });
        quotes.forEach(q => { q.contentEditable = !isEditing; });
        btn.innerText = isEditing ? "Edit Values" : "Save Changes";
    };

    init();
</script>
</body>
</html>
"""

def main():
    if not os.path.exists(INPUT_FILE): return
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    final_html = TEMPLATE.replace("{{DATA_JSON}}", json.dumps(data)).replace("{{CONFIG}}", json.dumps(TABLE_CONFIG))
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(final_html)
    webbrowser.open('file://' + os.path.realpath(OUTPUT_FILE))

if __name__ == "__main__":
    main()
