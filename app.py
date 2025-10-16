# app.py
from fastapi import FastAPI, Request, HTTPException
from config import STUDENT_SECRET, BASE_REPO_DIR, GITHUB_USERNAME
from pathlib import Path
from uuid import uuid4
import asyncio
import shutil
import json
import base64
import traceback
import requests

from github_utils import create_or_update_repo
from llm_generator import generate_app_from_brief

app = FastAPI()


@app.post("/api-endpoint")
async def api_endpoint(request: Request):
    """
    Primary endpoint for student app.
    Accepts {"email", "secret", "task", "round", "brief", "evaluation_url", ...}
    """
    try:
        data = await request.json()

        # 🔒 Verify secret
        if data.get("secret") != STUDENT_SECRET:
            raise HTTPException(status_code=403, detail="Invalid secret")

        # 🧠 Process asynchronously to immediately return HTTP 200
        asyncio.create_task(process_task(data))

        return {"status": "ok", "message": "Task received successfully"}
    except Exception as e:
        print("❌ Error in api-endpoint:", e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


async def process_task(data):
    """
    Handles creation or update of GitHub repo + notification to evaluation server.
    """
    try:
        email = data["email"]
        task_id = data["task"]
        round_num = int(data.get("round", 1))
        nonce = data.get("nonce", str(uuid4()))
        brief = data.get("brief", "")
        evaluation_url = data.get("evaluation_url")
        attachments = data.get("attachments", [])

        # 🎯 Create unique repo folder per round
        repo_folder = BASE_REPO_DIR / f"{task_id}_{nonce}_app"
        if repo_folder.exists():
            shutil.rmtree(repo_folder)
        repo_folder.mkdir(parents=True, exist_ok=True)

        # 📦 Save attachments
        attachments_dir = repo_folder / "attachments"
        attachments_dir.mkdir(exist_ok=True)
        for att in attachments:
            if "name" in att and "url" in att:
                name, url = att["name"], att["url"]
                if url.startswith("data:"):
                    _, b64data = url.split(",", 1)
                    with open(attachments_dir / name, "wb") as f:
                        f.write(base64.b64decode(b64data))

        # ⚙️ Generate app files for this round
        generate_app_from_brief(brief, attachments_dir, repo_folder)

        # 🪪 LICENSE + README
        (repo_folder / "LICENSE").write_text("MIT License")
        (repo_folder / "README.md").write_text(f"# {task_id}\n\n{brief}\n\nMIT License.")

        # 🚀 GitHub push (round-aware)
        repo_name, commit_sha, pages_url = create_or_update_repo(task_id, repo_folder, round_num)
        print("✅ GitHub push complete:", repo_name, commit_sha, pages_url)

        # 📡 Notify evaluation API
        if evaluation_url:
            await notify_evaluation_api(email, task_id, round_num, nonce, repo_name, commit_sha, pages_url, evaluation_url)

        # 🧩 Auto-trigger Round 2 task if Round 1 completed successfully
        if round_num == 1 and evaluation_url:
            await generate_round2_task(email, task_id, evaluation_url, brief)

    except Exception as e:
        print("❌ Task processing error:", e)
        traceback.print_exc()


async def notify_evaluation_api(email, task_id, round_num, nonce, repo_name, commit_sha, pages_url, evaluation_url):
    """
    Posts completion status to the instructor’s evaluation URL.
    """
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
        print(f"📤 Notifying evaluation API ({evaluation_url}) ...")
        r = await asyncio.to_thread(lambda: requests.post(evaluation_url, json=payload))

        if r.status_code != 200:
            print("⚠️ Evaluation API error:", r.status_code, r.text)
        else:
            print(f"✅ Evaluation API notified successfully for round {round_num}")
    except Exception as e:
        print("❌ Error notifying evaluation API:", e)
        traceback.print_exc()


async def generate_round2_task(email, task_id, evaluation_url, previous_brief):
    """
    Automatically triggers the instructor for round 2 task generation.
    """
    nonce = str(uuid4())
    payload = {
        "email": email,
        "secret": STUDENT_SECRET,
        "task": task_id,
        "round": 2,
        "nonce": nonce,
        "brief": f"Round 2 update for previous brief:\n{previous_brief}",
        "checks": [],
        "evaluation_url": evaluation_url,
        "attachments": []
    }

    try:
        print("📡 Triggering round 2 task ...")
        r = await asyncio.to_thread(lambda: requests.post(evaluation_url, json=payload))
        if r.status_code != 200:
            print("⚠️ Failed to notify round 2 evaluation API:", r.status_code, r.text)
        else:
            print("✅ Round 2 task notification sent successfully!")
    except Exception as e:
        print("❌ Error in round 2 task trigger:", e)
        traceback.print_exc()


@app.post("/eval-mock")
async def eval_mock(request: Request):
    """
    Local testing endpoint to mock the instructor’s evaluation server.
    """
    data = await request.json()
    print("✅ Eval mock received:\n", json.dumps(data, indent=2))
    return {"status": "received", "round": data.get("round")}
