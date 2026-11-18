"""Tiny .env loader shared by the register scripts (avoids a python-dotenv
dependency for a handful of KEY=VALUE lines)."""

import os
from pathlib import Path

REGISTER_ROOT = Path(__file__).resolve().parent.parent


def load_env(dotenv_path=None):
    path = Path(dotenv_path) if dotenv_path else REGISTER_ROOT / ".env"
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def db_path():
    load_env()
    return os.environ.get("DB_PATH", str(REGISTER_ROOT / "register.db"))
