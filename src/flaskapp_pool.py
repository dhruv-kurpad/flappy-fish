import cProfile
import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, request, jsonify, g
from postgrest.exceptions import APIError
from supabase import Client, create_client

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

app = Flask(__name__)

'''
PROFILE_DIR = Path(__file__).resolve().parent.parent / "profile_pool"
PROFILE_DIR.mkdir(parents=True, exist_ok=True)

@app.before_request
def start_profiler():
    g.profiler = cProfile.Profile()
    g.profiler.enable()


@app.after_request
def stop_profiler(response):
    g.profiler.disable()
    endpoint = request.endpoint or "unknown"
    g.profiler.dump_stats(PROFILE_DIR / f"{endpoint}.prof")
    return response
'''

PLAYERS_TABLE = "players"
UNIQUE_VIOLATION = "23505"


@lru_cache(maxsize=1)
def get_db() -> Client:
    return create_client(
        os.environ["SUPABASE_URL"],
        os.environ["SUPABASE_SECRET_KEY"],
    )


def public_player(row_dict):
    """Strip password before sending player data to clients."""
    if not row_dict:
        return None
    return {
        "id": row_dict.get("id"),
        "username": row_dict.get("username"),
        "high_score": row_dict.get("high_score", 0),
    }


@app.route("/getAllPlayers", methods=["GET"])
def get_all_players():
    try:
        result = get_db().table(PLAYERS_TABLE).select("*").execute()
        return jsonify(result.data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    username = data.get("username")
    password = data.get("password")

    try:
        result = (
            get_db()
            .table(PLAYERS_TABLE)
            .select("*")
            .eq("username", username)
            .eq("password", password)
            .limit(1)
            .execute()
        )

        if not result.data:
            return jsonify({"error": "Invalid username or password"}), 401

        return jsonify(public_player(result.data[0])), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    username = data.get("username")
    password = data.get("password")

    if not username or not str(username).strip():
        return jsonify({"code": -2, "error": "Username cannot be empty."}), 400
    if not password or not str(password).strip():
        return jsonify({"code": -3, "error": "Password cannot be empty."}), 400

    try:
        get_db().table(PLAYERS_TABLE).insert(
            {"username": username, "password": password}
        ).execute()
        return jsonify({"message": "Player added successfully"}), 201
    except APIError as e:
        if getattr(e, "code", None) == UNIQUE_VIOLATION:
            return jsonify({"error": "Username already taken"}), 409
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/delete", methods=["DELETE"])
def delete():
    data = request.get_json(silent=True) or {}
    username = data.get("username")

    try:
        get_db().table(PLAYERS_TABLE).delete().eq("username", username).execute()
        return jsonify({"message": f"Deleted user {username}"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/updateScore", methods=["PUT"])
def update_score():
    data = request.get_json(silent=True) or {}
    username = data.get("username")
    score = data.get("score")

    try:
        get_db().table(PLAYERS_TABLE).update(
            {"high_score": score}
        ).eq("username", username).execute()
        return jsonify({"message": f"Updated score for {username} to {score}"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/')
def hello_world():
    return 'Hello, World!'


if __name__ == "__main__":
    port = int(os.getenv("PORT", "80"))
    app.run(host="0.0.0.0", port=port)
