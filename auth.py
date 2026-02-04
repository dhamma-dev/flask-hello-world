"""
Flat-file user store and login helpers.
Users file: one line per user, "username:werkzeug_hash" (hash can contain colons).
"""
import os
from functools import wraps
from pathlib import Path

from flask import session, redirect, request, url_for
from werkzeug.security import check_password_hash

USER_FILE_ENV = "USER_FILE"
DEFAULT_USER_FILE = "users.txt"


def _user_file_path() -> Path:
    path = os.environ.get(USER_FILE_ENV, DEFAULT_USER_FILE)
    return Path(path)


def load_users() -> dict[str, str]:
    """Return dict of username -> password hash. Empty if file missing or unreadable."""
    users = {}
    path = _user_file_path()
    if not path.exists():
        return users
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if ":" in line:
                    username, hash_part = line.split(":", 1)
                    users[username.strip()] = hash_part.strip()
    except OSError:
        pass
    return users


def verify_user(username: str, password: str) -> bool:
    users = load_users()
    if username not in users:
        return False
    return check_password_hash(users[username], password)


def login_required(f):
    """Decorator: redirect to login if not in session. Webhook and health routes stay public."""
    @wraps(f)
    def wrapped(*args, **kwargs):
        if session.get("user") is None:
            return redirect(url_for("login", next=request.url))
        return f(*args, **kwargs)
    return wrapped
