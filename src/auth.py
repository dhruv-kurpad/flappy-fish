import requests

BASE_URL = "http://cs506x3a.cs.wisc.edu:8080/api/players"

def register_user(username, password):
    try:
        response = requests.get(
            f"{BASE_URL}/register",
            params={"name": username, "pwd": password},
            timeout=5,
        )
        response.raise_for_status()
    except requests.RequestException:
        return {"code": -99}

    return {"code": int(response.text)}

def login_user(username, password):
    try:
        response = requests.get(
            f"{BASE_URL}/login",
            params={"name": username, "pwd": password},
            timeout=5,
        )
        response.raise_for_status()
        data = response.json()
    except requests.RequestException:
        return {"code": -99}
    except ValueError:
        return {"code": -99}

    return data

def remove_user(username):
    try:
        response = requests.get(
            f"{BASE_URL}/remove",
            params={"name": username},
            timeout=5,
        )
        response.raise_for_status()
    except requests.RequestException:
        return {"code": -99}

    return {"code": int(response.text)}

def get_leaderboard():
    try:
        response = requests.get(
            f"{BASE_URL}/leaderboard",
            timeout=5,
        )
        response.raise_for_status()
        data = response.json()
    except requests.RequestException:
        return {
            "success": False,
            "message": "Cannot connect to Spring Boot backend.",
            "players": []
        }
    except ValueError:
        return {
            "success": False,
            "message": "Invalid response from backend.",
            "players": []
        }

    return {
        "success": True,
        "message": "Leaderboard loaded successfully.",
        "players": data
    }
