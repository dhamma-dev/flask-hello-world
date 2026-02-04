#!/usr/bin/env python3
"""
Add or update a user in the flat-file users list.
Usage: python scripts/add_user.py <username> <password>
       USER_FILE=/path/to/users.txt python scripts/add_user.py <username> <password>
"""
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from werkzeug.security import generate_password_hash

USER_FILE_ENV = "USER_FILE"
DEFAULT_USER_FILE = "users.txt"


def main():
    if len(sys.argv) != 3:
        print("Usage: add_user.py <username> <password>", file=sys.stderr)
        sys.exit(1)
    username, password = sys.argv[1], sys.argv[2]
    path = Path(os.environ.get(USER_FILE_ENV, DEFAULT_USER_FILE))
    if not path.is_absolute():
        path = Path(__file__).resolve().parent.parent / path
    path.parent.mkdir(parents=True, exist_ok=True)

    # Load existing and replace this user's line
    lines = []
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip().startswith("#"):
                    lines.append(line)
                elif ":" in line and line.split(":", 1)[0].strip() != username:
                    lines.append(line)

    hash_val = generate_password_hash(password, method="scrypt")
    lines.append(f"{username}:{hash_val}\n")

    with open(path, "w", encoding="utf-8") as f:
        f.writelines(lines)
    print(f"User {username!r} added/updated in {path}")


if __name__ == "__main__":
    main()
