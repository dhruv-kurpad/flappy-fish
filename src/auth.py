"""
auth.py handles player-related communication between the CLI and the Spring Boot backend.
Provides helper functions for registering users, logging in, removing users,and retrieving leaderboard data.
"""

import requests

# Base URL for all player-related backend API endpoints.
BASE_URL = "http://cs506x3a.cs.wisc.edu:8080/api/players"


# Register a user through the backend API and return a status code.
def register_user(username, password):
    try:
        response = requests.get(
            f"{BASE_URL}/register",
            # Pass the username and password as query parameters.
            params={"name": username, "pwd": password},
            # Stop waiting if the backend does not respond within 5 seconds.
            timeout=5,
        )
        # Raise an exception if the HTTP response indicates an error.
        response.raise_for_status()
    except requests.RequestException:
        # Return a special error code if the backend cannot be reached.
        return {"code": -99}

    # Convert the backend text response into an integer status code.
    return {"code": int(response.text)}


# Log in a user through the backend API and return the JSON response.
def login_user(username, password):
    try:
        response = requests.get(
            f"{BASE_URL}/login",
            # Pass the username and password as query parameters.
            params={"name": username, "pwd": password},
            # Stop waiting if the backend does not respond within 5 seconds.
            timeout=5,
        )
        # Raise an exception if the HTTP response indicates an error.
        response.raise_for_status()
        # Parse the backend response as JSON.
        data = response.json()
    except requests.RequestException:
        # Return a special error code if the backend cannot be reached.
        return {"code": -99}
    except ValueError:
        # Return the same error code if the response is not valid JSON.
        return {"code": -99}

    # Return the parsed login result directly.
    return data


# Remove a user through the backend API and return a status code.
def remove_user(username):
    try:
        response = requests.get(
            f"{BASE_URL}/remove",
            # Pass the username as a query parameter.
            params={"name": username},
            # Stop waiting if the backend does not respond within 5 seconds.
            timeout=5,
        )
        # Raise an exception if the HTTP response indicates an error.
        response.raise_for_status()
    except requests.RequestException:
        # Return a special error code if the backend cannot be reached.
        return {"code": -99}

    # Convert the backend text response into an integer status code.
    return {"code": int(response.text)}


# Retrieve leaderboard data from the backend API.
def get_leaderboard():
    try:
        response = requests.get(
            f"{BASE_URL}/leaderboard",
            # Stop waiting if the backend does not respond within 5 seconds.
            timeout=5,
        )
        # Raise an exception if the HTTP response indicates an error.
        response.raise_for_status()
        # Parse the leaderboard response as JSON.
        data = response.json()
    except requests.RequestException:
        # Return a failure result and an empty player list if the backend cannot be reached.
        return {
            "success": False,
            "message": "Cannot connect to Spring Boot backend.",
            "players": []
        }
    except ValueError:
        # Return a failure result and an empty player list if the response is not valid JSON.
        return {
            "success": False,
            "message": "Invalid response from backend.",
            "players": []
        }

    # Return the leaderboard data in a structured result dictionary.
    return {
        "success": True,
        "message": "Leaderboard loaded successfully.",
        "players": data
    }