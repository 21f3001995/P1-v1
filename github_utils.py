# github_utils.py
import subprocess
from pathlib import Path
from config import GITHUB_USERNAME

def create_and_push_repo(repo_name: str, repo_folder: Path):
    """
    Creates a GitHub repo, commits local files, and pushes.
    Returns: (repo_url, commit_sha, pages_url)
    """
    repo_folder = Path(repo_folder)
    repo_folder.mkdir(parents=True, exist_ok=True)

    # Initialize Git repo
    subprocess.run(["git", "-C", str(repo_folder), "init"], check=True)
    subprocess.run(["git", "-C", str(repo_folder), "add", "."], check=True)

    # Only commit if there are changes
    status = subprocess.run(
        ["git", "-C", str(repo_folder), "status", "--porcelain"],
        capture_output=True, text=True, check=True
    )
    if status.stdout.strip():
        subprocess.run(
            ["git", "-C", str(repo_folder), "commit", "-m", "Initial commit"],
            check=True
        )

    # Full repo name
    full_repo_name = f"{GITHUB_USERNAME}/{repo_name}"

    # Create repo & push using GH CLI
    result = subprocess.run([
        "gh", "repo", "create", full_repo_name,
        "--public", "--source", str(repo_folder), "--remote", "origin", "--push"
    ], capture_output=True, text=True)

    if result.returncode != 0:
        print("GitHub CLI failed!\nstdout:", result.stdout, "\nstderr:", result.stderr)
        raise subprocess.CalledProcessError(result.returncode, result.args)

    repo_url = f"https://github.com/{full_repo_name}"
    pages_url = f"https://{GITHUB_USERNAME}.github.io/{repo_name}/"

    # Get current commit SHA
    sha_result = subprocess.run(
        ["git", "-C", str(repo_folder), "rev-parse", "HEAD"],
        capture_output=True, text=True, check=True
    )
    commit_sha = sha_result.stdout.strip()

    return repo_name, commit_sha, pages_url
