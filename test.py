import markdown

# 1. Define the Dark Mode CSS
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
