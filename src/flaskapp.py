import cProfile
import pstats
from pathlib import Path
import os
import pyodbc
from flask import Flask, request, jsonify, g
from dbutils.pooled_db import PooledDB

app = Flask(__name__)

PROFILE_DIR = Path(__file__).resolve().parent.parent / "profiles"
PROFILE_DIR.mkdir(parents=True, exist_ok=True)


@app.before_request
def start_profiler():
    g.profiler = cProfile.Profile()
    g.profiler.enable()


@app.after_request
def stop_profiler(response):
    g.profiler.disable()
    filename = f"profiles/{request.endpoint}.prof"
    g.profiler.dump_stats(filename)
    return response


_CONNECTION_STRING = (
    "Driver={ODBC Driver 18 for SQL Server};"
    f"Server={os.getenv('SERVER')};"
    f"Database={os.getenv('DATABASE')};"
    f"Uid={os.getenv('UID')};"
    f"Pwd={os.getenv('PWD')};"
    "Encrypt=yes;"
    "TrustServerCertificate=yes;"
    "Connection Timeout=60;"
)

def _create_connection():
    return pyodbc.connect(_CONNECTION_STRING, timeout=60)


_create_connection.dbapi = pyodbc

_pool = PooledDB(
    creator=_create_connection,
    failures=(pyodbc.Error,),
    mincached=0,       # don't connect at import — Azure SQL may be paused
    maxcached=5,
    maxconnections=10,
    blocking=True,
    ping=1,            # verify connection when taken from pool
)


def row_to_dict(cursor, row):
    """Convert a pyodbc row tuple to a dict using column names."""
    if row is None:
        return None
    columns = [col[0] for col in cursor.description]
    return dict(zip(columns, row))


def public_player(row_dict):
    """Strip password before sending player data to clients."""
    if not row_dict:
        return None
    return {
        "id": row_dict.get("id"),
        "username": row_dict.get("username"),
        "high_score": row_dict.get("high_score", 0),
    }


def get_db():
    conn = pyodbc.connect(
            "Driver={ODBC Driver 18 for SQL Server};"
            "Server=tcp:flappy-fish.database.windows.net,1433;"
            "Database=flappy-fish;"
            "Uid=dkurpad;"
            "Pwd=FlappyFish67;"
            "Encrypt=yes;"
            "TrustServerCertificate=no;"
        )
    return conn

@app.route("/getAllPlayers", methods=["GET"])
def get_all_players():
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM dbo.players")
        rows = cursor.fetchall()
        players = [row_to_dict(cursor, row) for row in rows]
        conn.close()
        return jsonify(players)
    except pyodbc.Error as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    username = data.get("username")
    password = data.get("password")

    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        row = cursor.execute(
            "SELECT * FROM dbo.players WHERE username = ? AND password = ?",
            (username, password),
        ).fetchone()

        if row is None:
            return jsonify({"error": "Invalid username or password"}), 401

        result = public_player(row_to_dict(cursor, row))
        return jsonify(result), 200
    except pyodbc.Error as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn is not None:
            conn.close()

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
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO dbo.players (username, password) VALUES (?, ?)",
            (username, password),
        )
        conn.commit()
        conn.close()
        return jsonify({"message": "Player added successfully"}), 201
    except pyodbc.IntegrityError:
        return jsonify({"error": "Username already taken"}), 409
    except pyodbc.Error as e:
        return jsonify({"error": str(e)}), 500

@app.route("/delete", methods=["DELETE"])
def delete():
    data = request.get_json()
    username = data.get("username")

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM dbo.players WHERE username = ?", (username,))
    conn.commit()
    conn.close()

    return jsonify({"message": f"Deleted user {username}"}), 200
@app.route("/updateScore", methods=["PUT"])
def update_score():
    data = request.get_json()
    username = data.get("username")
    score = data.get("score")

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE dbo.players SET high_score = ? WHERE username = ?",
        (score, username)
    )
    conn.commit()
    conn.close()

    return jsonify({"message": f"Updated score for {username} to {score}"}), 200

@app.route('/')
def hello_world():
    return 'Hello, World!'

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5050"))
    app.run(host="0.0.0.0", port=port)


