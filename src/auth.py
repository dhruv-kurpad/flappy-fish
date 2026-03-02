import requests

BASE_URL = "http://localhost:8080/api/players"

def register_user(username, password):
    try:
        response = requests.get(
            f"{BASE_URL}/register",
            params={"name": username, "pwd": password},
            timeout=5,
        )
        response.raise_for_status()
    except requests.RequestException:
        return {"success": False, "message": "Cannot connect to Spring Boot backend."}

    message = response.text
    return {
        "success": "Registration Successful!" in message,
        "message": message,
    }

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
        return {"success": False, "message": "Cannot connect to Spring Boot backend."}
    except ValueError:
        return {"success": False, "message": "Invalid response from backend."}

    return {
        "success": bool(data.get("success")),
        "message": data.get("message", "Login request completed."),
    }