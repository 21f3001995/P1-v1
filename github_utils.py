# github_utils.py
import requests
import subprocess
from pathlib import Path
from config import GITHUB_USERNAME, GITHUB_TOKEN


def create_and_push_repo(repo_name: str, local_path: Path):
    """
    Creates a GitHub repo with the exact repo_name, pushes code, and enables Pages.
    Returns: (repo_name, latest_commit_sha, pages_url)
    """
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }

    # 1️⃣ Create repo
    payload = {"name": repo_name, "private": False, "auto_init": False}
    r = requests.post("https://api.github.com/user/repos", json=payload, headers=headers)

    if r.status_code not in [200, 201]:
        # If repo already exists, that’s fine; reuse it
        if "already exists" not in r.text:
            raise Exception(f"GitHub repo creation failed: {r.status_code} {r.text}")

    # 2️⃣ Local Git setup and push
    subprocess.run(["git", "init"], cwd=local_path, check=True)
    subprocess.run(["git", "branch", "-M", "main"], cwd=local_path, check=True)
    subprocess.run(["git", "add", "."], cwd=local_path, check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=local_path, check=True)
    remote_url = f"https://{GITHUB_USERNAME}:{GITHUB_TOKEN}@github.com/{GITHUB_USERNAME}/{repo_name}.git"
    subprocess.run(["git", "remote", "add", "origin", remote_url], cwd=local_path, check=True)
    subprocess.run(["git", "push", "-u", "origin", "main"], cwd=local_path, check=True)

    # 3️⃣ Enable GitHub Pages
    pages_api_url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{repo_name}/pages"
    pages_payload = {"source": {"branch": "main", "path": "/"}}
    r_pages = requests.post(pages_api_url, headers=headers, json=pages_payload)
    if r_pages.status_code not in [201, 204]:
        print(f"⚠️ Pages activation warning: {r_pages.status_code} - {r_pages.text}")

    # 4️⃣ Get commit SHA
    result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=local_path, capture_output=True, text=True)
    commit_sha = result.stdout.strip() if result.returncode == 0 else "N/A"

    pages_url = f"https://{GITHUB_USERNAME}.github.io/{repo_name}/"
    return repo_name, commit_sha, pages_url
