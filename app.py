# app.py
from fastapi import FastAPI, Request, HTTPException
from config import STUDENT_SECRET, BASE_REPO_DIR, GITHUB_USERNAME, GITHUB_TOKEN
from pathlib import Path
from uuid import uuid4
import asyncio
import shutil
import json
import base64
import subprocess
import requests

from github_utils import create_and_push_repo
from llm_generator import generate_app_from_brief

app = FastAPI()

@app.post("/api-endpoint")
async def api_endpoint(request: Request):
    data = await request.json()

    # Secret verification
    if data.get("secret") != STUDENT_SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret")

    # Process the task asynchronously
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

        # Create unique repo folder
        repo_folder = BASE_REPO_DIR / f"{task_id}_{nonce}_app"
        if repo_folder.exists():
            shutil.rmtree(repo_folder)
        repo_folder.mkdir(parents=True)

        attachments_dir = repo_folder / "attachments"
        attachments_dir.mkdir(exist_ok=True)

        # Save attachments
        for att in attachments:
            if "name" in att and "url" in att:
                name, url = att["name"], att["url"]
                if url.startswith("data:"):
                    _, b64data = url.split(",", 1)
                    with open(attachments_dir / name, "wb") as f:
                        f.write(base64.b64decode(b64data))

        # Generate app files (HTML/JS)
        generate_app_from_brief(brief, attachments_dir, repo_folder)

        # LICENSE
        (repo_folder / "LICENSE").write_text("MIT License")

        # README
        (repo_folder / "README.md").write_text(f"# {task_id}\n\n{brief}\n\nMIT License.")

        # GitHub: create repo & push
        repo_name, commit_sha, pages_url = create_and_push_repo(task_id, repo_folder)

        print("GH output:", repo_name, commit_sha, pages_url)

        # Notify evaluation API
        await notify_evaluation_api(email, task_id, round_num, nonce, repo_name, commit_sha, pages_url, evaluation_url)

        # Auto-generate round 2 task if round 1
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
        "repo_url": f"https://github.com/{GITHUB_USERNAME}/{repo_name}",
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


@app.post("/eval-mock")
async def eval_mock(request: Request):
    data = await request.json()
    print("✅ Eval mock received:", json.dumps(data, indent=2))
    return {"status": "received"}

