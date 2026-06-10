"""
auth.py handles player-related communication between the CLI / game server
and the Flask API (flaskapp.py) backed by Azure SQL.
"""

import os
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# Flask API — default matches flaskapp_pool.py on port 80.
BASE_URL = (os.getenv("BASE_URL"))


def register_user(username, password):
    if not username or not str(username).strip():
        return {"code": -2}
    if not password or not str(password).strip():
        return {"code": -3}

    try:
        response = requests.post(
            f"{BASE_URL}/register",
            json={"username": username, "password": password},
            timeout=5,
        )
        if response.status_code == 201:
            return {"code": 0}
        if response.status_code == 409:
            return {"code": -1}
        if response.status_code == 400:
            data = response.json()
            return {"code": data.get("code", -99)}
    except requests.RequestException:
        return {"code": -99}

    return {"code": -99}


def login_user(username, password):
    if not username or not str(username).strip():
        return {"code": -2}

    try:
        response = requests.post(
            f"{BASE_URL}/login",
            json={"username": username, "password": password},
            timeout=5,
        )
        if response.status_code == 401:
            return {"code": -1}
        response.raise_for_status()
        data = response.json()
    except requests.RequestException:
        return {"code": -99}
    except ValueError:
        return {"code": -99}

    return {
        "code": 0,
        "username": data.get("username"),
        "playerId": data.get("id"),
        "highScore": data.get("high_score", 0),
    }


def remove_user(username):
    try:
        response = requests.delete(
            f"{BASE_URL}/delete",
            json={"username": username},
            timeout=5,
        )
        if response.status_code == 404:
            return {"code": -1}
        response.raise_for_status()
    except requests.RequestException:
        return {"code": -99}

    return {"code": 0}


def get_leaderboard():
    try:
        response = requests.get(f"{BASE_URL}/getAllPlayers", timeout=5)
        response.raise_for_status()
        raw = response.json()
    except requests.RequestException:
        return {
            "success": False,
            "message": "Cannot connect to Flask backend.",
            "players": [],
        }
    except ValueError:
        return {
            "success": False,
            "message": "Invalid response from backend.",
            "players": [],
        }

    players = [
        {
            "username": row.get("username"),
            "highScore": row.get("high_score", 0),
        }
        for row in raw
        if row.get("username")
    ]
    players.sort(key=lambda p: p["highScore"], reverse=True)

    return {
        "success": True,
        "message": "Leaderboard loaded successfully.",
        "players": players,
    }


def update_score(username, score):
    try:
        response = requests.put(
            f"{BASE_URL}/updateScore",
            json={"username": username, "score": score},
            timeout=5,
        )
        if response.status_code == 404:
            return {"code": -1}
        response.raise_for_status()
        data = response.json()
        return {"code": data.get("code", 0)}
    except requests.RequestException:
        return {"code": -99}
    except ValueError:
        return {"code": -99}
