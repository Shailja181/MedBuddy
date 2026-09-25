import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-change-me-in-production")
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{BASE_DIR / 'database' / 'medbuddy.db'}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = str(BASE_DIR / "uploads")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")