# config.py
from dotenv import load_dotenv
import os

load_dotenv()  # reads .env

STUDENT_SECRET = os.getenv("STUDENT_SECRET")
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
BASE_REPO_DIR = os.getenv("BASE_REPO_DIR", "tmp")
