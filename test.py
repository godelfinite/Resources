import markdown

# 1. Define the Dark Mode CSS
light_wide_style = """
<style>
    body {
        background-color: #ffffff;
        color: #000000;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
        line-height: 1.5;
        padding: 20px;
        margin: 0;
        width: 100%; /* Ensures full screen usage */
    }
    h1, h2, h3 {
        border-bottom: 1px solid #eaecef;
        padding-bottom: 0.3em;
    }
    table {
        border-collapse: collapse;
        width: 100%; /* Table expands to full container width */
        margin: 20px 0;
        font-size: 14px;
    }
    th, td {
        border: 1px solid #d0d7de;
        padding: 10px;
        text-align: left;
    }
    th {
        background-color: #f6f8fa;
        font-weight: 600;
    }
    tr:nth-child(even) {
        background-color: #f9f9f9;
    }
    /* Simple responsiveness for very small screens */
    @media (max-width: 768px) {
        body { padding: 10px; }
    }
</style>
"""
dark_style = """
<style>
    body {
        background-color: #121212;
        color: #ffffff;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        line-height: 1.6;
        padding: 40px;
        max-width: 900px;
        margin: auto;
    }
    table {
        border-collapse: collapse;
        width: 100%;
        margin: 20px 0;
        background-color: #1e1e1e;
    }
    th, td {
        border: 1px solid #444;
        padding: 12px;
        text-align: left;
    }
    th {
        background-color: #333;
        color: #00ff99; /* Subtle green for headers to make them pop */
    }
    tr:nth-child(even) {
        background-color: #1a1a1a;
    }
    code {
        background-color: #2d2d2d;
        padding: 2px 5px;
        border-radius: 4px;
        color: #f8f8f2;
    }
</style>
"""

# 2. Read your existing Markdown file
with open('SOP_Structure.md', 'r', encoding='utf-8') as f:
    md_content = f.read()

# 3. Convert Markdown to HTML (Enabling tables with 'extra')
html_content = markdown.markdown(md_content, extensions=['extra'])

# 4. Combine Style + Content and Save
full_html = f"<html><head>{dark_style}</head><body>{html_content}</body></html>"

with open('SOP_Structure.html', 'w', encoding='utf-8') as f:
    f.write(full_html)

print("Successfully generated Dark Mode SOP!")
