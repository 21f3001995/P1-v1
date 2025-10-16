import requests
import subprocess
import shutil
from pathlib import Path
from config import GITHUB_USERNAME, GITHUB_TOKEN


def run(cmd, cwd=None, check=True):
    """Utility: run shell command and show output."""
    print(f"🧩 {cmd}")
    result = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr)
    if check and result.returncode != 0:
        raise RuntimeError(f"Command failed: {cmd}\n{result.stderr}")
    return result


def create_or_update_repo(repo_name: str, local_path: Path, round_num: int):
    """
    Creates or updates a GitHub repo depending on round_num.
    Round 1 → create + initial push.
    Round 2 → pull + modify + recommit + push.
    Returns: (repo_name, latest_commit_sha, pages_url)
    """

    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }

    remote_url = f"https://{GITHUB_USERNAME}:{GITHUB_TOKEN}@github.com/{GITHUB_USERNAME}/{repo_name}.git"
    pages_url = f"https://{GITHUB_USERNAME}.github.io/{repo_name}/"

    # 🌀 Round 1: create repo fresh
    if round_num == 1:
        print(f"🚀 Round 1: Creating new repo {repo_name}...")

        payload = {"name": repo_name, "private": False, "auto_init": False}
        r = requests.post("https://api.github.com/user/repos", json=payload, headers=headers)
        if r.status_code not in [200, 201]:
            if "already exists" not in r.text:
                raise Exception(f"GitHub repo creation failed: {r.status_code} {r.text}")

        # Initialize Git
        run(["git", "init"], cwd=local_path)
        run(["git", "branch", "-M", "main"], cwd=local_path)
        run(["git", "config", "user.name", GITHUB_USERNAME], cwd=local_path)
        run(["git", "config", "user.email", "21f3001995@ds.study.iitm.ac.in"], cwd=local_path)
        run(["git", "add", "."], cwd=local_path)
        run(["git", "commit", "-m", "Initial commit"], cwd=local_path)
        run(["git", "remote", "add", "origin", remote_url], cwd=local_path)
        run(["git", "push", "-u", "origin", "main"], cwd=local_path)

        # Enable GitHub Pages
        pages_api_url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{repo_name}/pages"
        pages_payload = {"source": {"branch": "main", "path": "/"}}
        r_pages = requests.post(pages_api_url, headers=headers, json=pages_payload)
        if r_pages.status_code not in [201, 204]:
            print(f"⚠️ Pages activation warning: {r_pages.status_code} - {r_pages.text}")

    else:
        # 🌀 Round 2 or later: clone, modify, recommit, push
        print(f"🔁 Round {round_num}: Updating existing repo {repo_name}...")

        tmp_clone = local_path.parent / f"{repo_name}_clone"
        if tmp_clone.exists():
            shutil.rmtree(tmp_clone)
        run(["git", "clone", remote_url, str(tmp_clone)])

        # Copy updated files from local_path into cloned repo
        for item in local_path.iterdir():
            if item.name == ".git":
                continue
            dest = tmp_clone / item.name
            if item.is_dir():
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.copytree(item, dest)
            else:
                shutil.copy2(item, dest)

        # Commit & push updates
        run(["git", "config", "user.name", GITHUB_USERNAME], cwd=tmp_clone)
        run(["git", "config", "user.email", "21f3001995@ds.study.iitm.ac.in"], cwd=tmp_clone)
        run(["git", "add", "."], cwd=tmp_clone)
        run(["git", "commit", "-m", f"Round {round_num} update"], cwd=tmp_clone, check=False)
        run(["git", "pull", "--rebase", "origin", "main"], cwd=tmp_clone, check=False)
        run(["git", "push", "origin", "main"], cwd=tmp_clone, check=False)

    # Get latest commit SHA
    result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=local_path, capture_output=True, text=True)
    commit_sha = result.stdout.strip() if result.returncode == 0 else "N/A"

    print(f"✅ {repo_name} pushed successfully (Round {round_num}) — commit {commit_sha}")
    return repo_name, commit_sha, pages_url
