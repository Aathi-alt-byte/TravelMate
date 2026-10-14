"""Shared application settings used by the Flask app and booking module."""

import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

try:
    from dotenv import load_dotenv

    load_dotenv(BASE_DIR / ".env")
except ImportError:
    # Environment variables can still be supplied by the operating system.
    pass

DATABASE_PATH = Path(
    os.environ.get("TRAVELMATE_DATABASE", BASE_DIR / "instance" / "travelmate.sqlite3")
)
