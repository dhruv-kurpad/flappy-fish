import requests

BASE_URL = "http://localhost:8080/api/players"

def register_user(username, password):
    r = requests.get(f"{BASE_URL}/register", params={"name": username, "pwd": password})
    return {"success": (r.status_code == 200), "message": r.text}

def login_user(username, password):
    r = requests.get(f"{BASE_URL}/all")
    return {"success": (r.status_code == 200), "message": "Connected to Spring Boot!" if r.status_code==200 else r.text}