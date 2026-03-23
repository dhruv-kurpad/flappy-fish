#!/usr/bin/env python3
"""
File to update the backend with fake users and scores

"""
from __future__ import annotations

import json
import random
from pathlib import Path

from auth import register_user, update_score

# Repo root: src/populate.py -> ../test_users.json
JSON = Path(__file__).resolve().parent.parent / "test_users.json"


def populate_from_json() -> None:
    """Read JSON, register each user, assign a random high score 1–100."""
    #load json and do a general formatting check
    data = json.loads(JSON.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("JSON root must be a list of user objects.")
    #loop through all users, register them, then update their high score
    for i, entry in enumerate(data, start=1):
        username = entry.get("username")
        password = entry.get("password")
        # Line read from json is not a username and password that can be understood
        if not username or not password:
            print(f"[{i}] skip: missing username or password: {entry!r}")
            continue

        reg = register_user(username, password)
        code = reg.get("code")
        # Something went wrong when registering the user, skip to next set of usernames and passwords
        if code not in (0, -1):
            print(f"[{i}] {username}: register returned {code}, skipping score")
            continue

        # Generate a random high score between 1 and 100
        score = random.randint(1, 100)
        # Update the high score with the backend API
        upd = update_score(username, score)
        upd_code = upd.get("code")
        # Something went wrong when updating the high score, skip to next set of usernames and passwords
        if upd_code == -99:
            print(f"[{i}] {username}: Can't reach backend)")
            continue


def main() -> None:
    if not JSON.is_file():
        raise SystemExit(f"File not found: {JSON}")
    populate_from_json()


if __name__ == "__main__":
    main()
