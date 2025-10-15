# app.py
from fastapi import FastAPI, Request, HTTPException
from config import STUDENT_SECRET, BASE_REPO_DIR
from github_utils import create_and_push_repo
from uuid import uuid4
from pathlib import Path
import asyncio
import shutil
import json
import requests

app = FastAPI()


@app.post("/api-endpoint")
async def api_endpoint(request: Request):
    data = await request.json()

    # Secret verification
    if data.get("secret") != STUDENT_SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret")

    # Return 200 OK immediately
    asyncio.create_task(process_task(data))
    return {"status": "ok"}


async def process_task(data):
    try:
        email = data["email"]
        task_id = data["task"]
        round_num = data["round"]
        nonce = data.get("nonce", str(uuid4()))
        brief = data.get("brief", "")
        evaluation_url = data.get("evaluation_url")
        attachments = data.get("attachments", [])

        # Create temp folder
        repo_folder = BASE_REPO_DIR / f"{task_id}_{nonce}_app"
        if repo_folder.exists():
            shutil.rmtree(repo_folder)
        repo_folder.mkdir(parents=True)

        # Create minimal files
        index_file = repo_folder / "index.html"
        index_file.write_text(f"<html><body><h1>{brief}</h1></body></html>")

        # LICENSE
        (repo_folder / "LICENSE").write_text("MIT License")

        # README
        (repo_folder / "README.md").write_text(f"# {task_id}\n\n{brief}\n\nMIT License.")

        # GitHub: create repo, push
        repo_name, commit_sha, pages_url = create_and_push_repo(task_id, repo_folder)

        print("GH output:", repo_name, commit_sha, pages_url)

        # Notify evaluation API
        await notify_evaluation_api(email, task_id, round_num, nonce, repo_name, commit_sha, pages_url, evaluation_url)

        # Optionally, simulate round 2 task generation (instructors would normally do this)
        if round_num == 1 and evaluation_url:
            await generate_round2_task(email, task_id, evaluation_url)

    except Exception as e:
        print("Task exception:", e)


async def notify_evaluation_api(email, task_id, round_num, nonce, repo_name, commit_sha, pages_url, evaluation_url):
    payload = {
        "email": email,
        "task": task_id,
        "round": round_num,
        "nonce": nonce,
        "repo_url": f"https://github.com/{repo_name}",
        "commit_sha": commit_sha,
        "pages_url": pages_url
    }
    try:
        r = await asyncio.to_thread(lambda: requests.post(evaluation_url, json=payload))
        if r.status_code != 200:
            print("Failed to notify evaluation API:", r.status_code, r.text)
        else:
            print(f"Evaluation API notified for round {round_num}")
    except Exception as e:
        print("Error notifying evaluation API:", e)


async def generate_round2_task(email, task_id, evaluation_url):
    from uuid import uuid4
    nonce = str(uuid4())
    payload = {
        "email": email,
        "secret": STUDENT_SECRET,
        "task": task_id,
        "round": 2,
        "nonce": nonce,
        "brief": "Instructor round 2 task",
        "checks": [],
        "evaluation_url": evaluation_url,
        "attachments": []
    }
    try:
        r = await asyncio.to_thread(lambda: requests.post(evaluation_url, json=payload))
        if r.status_code != 200:
            print("Failed to notify round 2 evaluation API:", r.status_code, r.text)
        else:
            print("Round 2 task notification sent successfully!")
    except Exception as e:
        print("Error in round 2 task:", e)
