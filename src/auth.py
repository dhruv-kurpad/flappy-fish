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
BASE_URL = os.getenv("BASE_URL")

DB_ASLEEP_MSG = "Databass is asleep, float around while the guppys wake him up"
_WAKE_USER = "tester"
_WAKE_PASS = "pass"
_REQUEST_TIMEOUT = 5
_RETRY_TIMEOUT = 15
_WAKE_TIMEOUT = 60


def _db_asleep_response():
    return {"code": -99, "message": DB_ASLEEP_MSG}


def _wake_database():
    """POST login as tester/pass to wake paused Azure SQL serverless DB."""
    try:
        requests.post(
            f"{BASE_URL}/login",
            json={"username": _WAKE_USER, "password": _WAKE_PASS},
            timeout=_WAKE_TIMEOUT,
        )
    except requests.RequestException:
        pass  # 401 still means Flask + DB responded; connection errors are ok to ignore


def _request_failed(response=None, exc=None):
    if exc is not None:
        return True
    return response is not None and response.status_code >= 500


def register_user(username, password):
    if not username or not str(username).strip():
        return {"code": -2}
    if not password or not str(password).strip():
        return {"code": -3}

    for attempt, timeout in enumerate((_REQUEST_TIMEOUT, _RETRY_TIMEOUT)):
        try:
            response = requests.post(
                f"{BASE_URL}/register",
                json={"username": username, "password": password},
                timeout=timeout,
            )
            if response.status_code == 201:
                return {"code": 0}
            if response.status_code == 409:
                return {"code": -1}
            if response.status_code == 400:
                data = response.json()
                return {"code": data.get("code", -99)}
            if _request_failed(response=response):
                if attempt == 0:
                    _wake_database()
                    continue
                return _db_asleep_response()
        except requests.RequestException:
            if attempt == 0:
                _wake_database()
                continue
            return _db_asleep_response()

    return _db_asleep_response()


def login_user(username, password):
    if not username or not str(username).strip():
        return {"code": -2}

    for attempt, timeout in enumerate((_REQUEST_TIMEOUT, _RETRY_TIMEOUT)):
        try:
            response = requests.post(
                f"{BASE_URL}/login",
                json={"username": username, "password": password},
                timeout=timeout,
            )
            if response.status_code == 401:
                return {"code": -1}
            if _request_failed(response=response):
                if attempt == 0:
                    _wake_database()
                    continue
                return _db_asleep_response()
            response.raise_for_status()
            data = response.json()
            return {
                "code": 0,
                "username": data.get("username"),
                "playerId": data.get("id"),
                "highScore": data.get("high_score", 0),
            }
        except requests.RequestException:
            if attempt == 0:
                _wake_database()
                continue
            return _db_asleep_response()
        except ValueError:
            if attempt == 0:
                _wake_database()
                continue
            return _db_asleep_response()

    return _db_asleep_response()


def remove_user(username):
    for attempt, timeout in enumerate((_REQUEST_TIMEOUT, _RETRY_TIMEOUT)):
        try:
            response = requests.delete(
                f"{BASE_URL}/delete",
                json={"username": username},
                timeout=timeout,
            )
            if response.status_code == 404:
                return {"code": -1}
            if _request_failed(response=response):
                if attempt == 0:
                    _wake_database()
                    continue
                return _db_asleep_response()
            response.raise_for_status()
            return {"code": 0}
        except requests.RequestException:
            if attempt == 0:
                _wake_database()
                continue
            return _db_asleep_response()

    return _db_asleep_response()


def get_leaderboard():
    for attempt, timeout in enumerate((_REQUEST_TIMEOUT, _RETRY_TIMEOUT)):
        try:
            response = requests.get(f"{BASE_URL}/getAllPlayers", timeout=timeout)
            if _request_failed(response=response):
                if attempt == 0:
                    _wake_database()
                    continue
                return {
                    "success": False,
                    "message": DB_ASLEEP_MSG,
                    "players": [],
                }
            response.raise_for_status()
            raw = response.json()
            break
        except requests.RequestException:
            if attempt == 0:
                _wake_database()
                continue
            return {
                "success": False,
                "message": DB_ASLEEP_MSG,
                "players": [],
            }
        except ValueError:
            if attempt == 0:
                _wake_database()
                continue
            return {
                "success": False,
                "message": "Invalid response from backend.",
                "players": [],
            }
    else:
        return {
            "success": False,
            "message": DB_ASLEEP_MSG,
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
    for attempt, timeout in enumerate((_REQUEST_TIMEOUT, _RETRY_TIMEOUT)):
        try:
            response = requests.put(
                f"{BASE_URL}/updateScore",
                json={"username": username, "score": score},
                timeout=timeout,
            )
            if response.status_code == 404:
                return {"code": -1}
            if _request_failed(response=response):
                if attempt == 0:
                    _wake_database()
                    continue
                return _db_asleep_response()
            response.raise_for_status()
            data = response.json()
            return {"code": data.get("code", 0)}
        except requests.RequestException:
            if attempt == 0:
                _wake_database()
                continue
            return _db_asleep_response()
        except ValueError:
            if attempt == 0:
                _wake_database()
                continue
            return _db_asleep_response()

    return _db_asleep_response()
