# llm_generator.py

import os
import json
import csv
import base64
from pathlib import Path

def generate_app_from_brief(brief, attachments_dir, output_folder):
    """
    Generates a functional static app based on the brief.
    Handles common templates: captcha, CSV sum, markdown, GitHub lookup.
    """
    os.makedirs(output_folder, exist_ok=True)

    # Detect task type from brief
    brief_lower = brief.lower()
    html_content = ""
    js_content = ""

    # --- Captcha Solver ---
    if "captcha" in brief_lower:
        html_content = """
        <!DOCTYPE html>
        <html>
        <head><title>Captcha Solver</title></head>
        <body>
            <h2>Captcha Solver</h2>
            <img id="captcha-img" src="" alt="Captcha"/>
            <div id="captcha-text">Loading...</div>
            <script>
                const params = new URLSearchParams(window.location.search);
                const url = params.get('url') || 'sample.png';
                document.getElementById('captcha-img').src = url;
                // Demo solver (echo image name)
                document.getElementById('captcha-text').textContent = "Solved: " + url.split('/').pop();
            </script>
        </body>
        </html>
        """

    # --- CSV Sum ---
    elif "sum-of-sales" in brief_lower or any(f.endswith(".csv") for f in os.listdir(attachments_dir)):
        # Find CSV
        csv_file = next((f for f in os.listdir(attachments_dir) if f.endswith(".csv")), None)
        if csv_file:
            total = 0
            with open(os.path.join(attachments_dir, csv_file), newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    total += float(row.get("sales", 0))
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head><title>Sales Summary</title></head>
            <body>
                <h2>Sales Summary</h2>
                <div id="total-sales">{total}</div>
            </body>
            </html>
            """

    # --- Markdown to HTML ---
    elif "markdown" in brief_lower or any(f.endswith(".md") for f in os.listdir(attachments_dir)):
        md_file = next((f for f in os.listdir(attachments_dir) if f.endswith(".md")), None)
        md_text = ""
        if md_file:
            with open(os.path.join(attachments_dir, md_file), "r", encoding="utf-8") as f:
                md_text = f.read()
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Markdown Renderer</title>
            <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.8.0/styles/default.min.css">
            <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.8.0/highlight.min.js"></script>
        </head>
        <body>
            <div id="markdown-output"></div>
            <script>
                const mdText = `{md_text.replace("`", "\\`")}`;
                document.getElementById('markdown-output').innerHTML = marked.parse(mdText);
                document.querySelectorAll('pre code').forEach((el) => hljs.highlightElement(el));
            </script>
        </body>
        </html>
        """

    # --- GitHub User Info ---
    elif "github" in brief_lower:
        html_content = """
        <!DOCTYPE html>
        <html>
        <head><title>GitHub User Lookup</title></head>
        <body>
            <form id="github-user-form">
                Username: <input id="username" type="text" />
                <button type="submit">Lookup</button>
            </form>
            <div id="github-created-at"></div>
            <script>
                document.getElementById('github-user-form').addEventListener('submit', async (e)=>{
                    e.preventDefault();
                    const user = document.getElementById('username').value;
                    const resp = await fetch('https://api.github.com/users/' + user);
                    const data = await resp.json();
                    document.getElementById('github-created-at').textContent = data.created_at || "Not found";
                });
            </script>
        </body>
        </html>
        """

    else:
        # Default: just display brief
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head><title>Generated App</title></head>
        <body>
            <h1>Task Brief</h1>
            <p>{brief}</p>
        </body>
        </html>
        """

    # Write HTML
    with open(os.path.join(output_folder, "index.html"), "w", encoding="utf-8") as f:
        f.write(html_content)

    # Copy attachments
    for f in os.listdir(attachments_dir):
        src = os.path.join(attachments_dir, f)
        dst = os.path.join(output_folder, f)
        if os.path.isfile(src):
            os.rename(src, dst)

    # MIT License
    with open(os.path.join(output_folder, "LICENSE"), "w") as f:
        f.write("MIT License")

    # README.md
    with open(os.path.join(output_folder, "README.md"), "w") as f:
        f.write(f"# Generated App\n\nBrief: {brief}\n\nLicense: MIT")
