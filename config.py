# config.py
from dotenv import load_dotenv
import os
from pathlib import Path

load_dotenv()  # reads .env

# Student secret to verify instructor requests
STUDENT_SECRET = os.getenv("STUDENT_SECRET")

# GitHub credentials
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# Local base path for repo creation
BASE_REPO_DIR = Path(os.getenv("BASE_REPO_DIR", "./repos"))

# OpenAI API key for LLM generation
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
