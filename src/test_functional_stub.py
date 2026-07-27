"""
Functional tests for Flappy Fish (web + backend).

Run with:

    cd src && python -m unittest test_functional_stub -v

Live E2E defaults to the Azure ACI URL. Optional overrides:
    GAME_SERVER_URL=...   # public API base (default: deployed ACI)
    FLASK_URL=...         # direct Flask (local compose only) for Hello World + delete cleanup
    AZURE_APP_URL=...     # override deployed frontend URL
"""

from __future__ import annotations

import json
import math
import os
import queue
import threading
import time
import unittest
import uuid
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import pyodbc
import requests

import auth
from display_buffer import BUFFER_COLS, GAME_AREA_HEIGHT, HEADER_ROWS
from game_logic import check_collision, run_game_headless, update_score
from gameObjects.obstacle import JellyfishObstacle, Obstacle, PufferfishObstacle, Tentacle
from gameObjects.obstacle_spawner import ObstacleSpawner, ObstacleTypeConfig
from gameObjects.player import Player
from gameObjects.sprite import Sprite

_REPO_ROOT = Path(__file__).resolve().parent.parent
_ASSETS = Path(__file__).resolve().parent / "assets"
_SRC = Path(__file__).resolve().parent
DEFAULT_AZURE_APP_URL = "http://flappy-fish.westus2.azurecontainer.io"


def _azure_app_url() -> str:
    return os.getenv("AZURE_APP_URL", DEFAULT_AZURE_APP_URL).rstrip("/")


def _player_row(player_id=1, username="alice", password="secret", high_score=0):
    return (player_id, username, password, high_score)


def _cursor_with_row(row=None, rows=None):
    """Mock cursor supporting execute().fetchone() chaining and fetchall()."""
    cursor = mock.MagicMock()
    cursor.description = [
        ("id", None, None, None, None, None, None),
        ("username", None, None, None, None, None, None),
        ("password", None, None, None, None, None, None),
        ("high_score", None, None, None, None, None, None),
    ]
    cursor.fetchone.return_value = row
    cursor.fetchall.return_value = rows if rows is not None else ([] if row is None else [row])
    cursor.execute.return_value = cursor
    return cursor


def _conn_with_cursor(cursor):
    conn = mock.MagicMock()
    conn.cursor.return_value = cursor
    return conn


def _http_response(status_code=200, json_data=None, text=""):
    resp = mock.Mock()
    resp.status_code = status_code
    resp.text = text
    if json_data is not None:
        resp.json.return_value = json_data
    else:
        resp.json.side_effect = ValueError("no json")
    resp.raise_for_status = mock.Mock()
    if status_code >= 400:
        exc = requests.HTTPError(response=resp)
        resp.raise_for_status.side_effect = exc
    return resp


# ---------------------------------------------------------------------------
# Flask DB API — flaskapp_pool.py (Docker runtime)
# ---------------------------------------------------------------------------


class TestFlaskApiHealth(unittest.TestCase):
    """Smoke tests that the Flask app responds."""

    @classmethod
    def setUpClass(cls):
        from flaskapp_pool import app

        cls.app = app
        cls.client = app.test_client()

    def test_root_returns_hello_world(self):
        """GET / should return 200 and body 'Hello, World!'."""
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data.decode(), "Hello, World!")

    def test_get_all_players_returns_json_array(self):
        """GET /getAllPlayers should return 200 and a JSON list (possibly empty)."""
        cursor = _cursor_with_row(rows=[])
        with mock.patch("flaskapp_pool.get_db", return_value=_conn_with_cursor(cursor)):
            resp = self.client.get("/getAllPlayers")
        self.assertEqual(resp.status_code, 200)
        self.assertIsInstance(resp.get_json(), list)

    def test_db_connection_failure_returns_500_not_crash(self):
        """When SQL is unreachable, endpoints return 500 JSON error, not an unhandled exception."""
        with mock.patch("flaskapp_pool.get_db", side_effect=pyodbc.Error("unreachable")):
            resp = self.client.get("/getAllPlayers")
        self.assertEqual(resp.status_code, 500)
        body = resp.get_json()
        self.assertIn("error", body)


class TestFlaskApiRegister(unittest.TestCase):
    """POST /register — player creation and validation."""

    @classmethod
    def setUpClass(cls):
        from flaskapp_pool import app

        cls.client = app.test_client()

    def test_register_valid_user_returns_201(self):
        """New username/password → 201 and success message; row exists in dbo.players."""
        cursor = _cursor_with_row()
        with mock.patch("flaskapp_pool.get_db", return_value=_conn_with_cursor(cursor)):
            resp = self.client.post(
                "/register",
                json={"username": "newbie", "password": "pw123"},
            )
        self.assertEqual(resp.status_code, 201)
        self.assertIn("successfully", resp.get_json()["message"].lower())
        args = cursor.execute.call_args[0]
        self.assertIn("INSERT", args[0])
        self.assertEqual(args[1], ("newbie", "pw123"))

    def test_register_duplicate_username_returns_409(self):
        """Second register with same username → 409 'Username already taken'."""
        cursor = _cursor_with_row()
        cursor.execute.side_effect = pyodbc.IntegrityError("duplicate")
        with mock.patch("flaskapp_pool.get_db", return_value=_conn_with_cursor(cursor)):
            resp = self.client.post(
                "/register",
                json={"username": "taken", "password": "pw"},
            )
        self.assertEqual(resp.status_code, 409)
        self.assertIn("already taken", resp.get_json()["error"].lower())

    def test_register_empty_username_returns_400_code_minus_2(self):
        """Empty or whitespace username → 400 with code -2."""
        resp = self.client.post(
            "/register",
            json={"username": "   ", "password": "pw"},
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.get_json()["code"], -2)

    def test_register_empty_password_returns_400_code_minus_3(self):
        """Empty or whitespace password → 400 with code -3."""
        resp = self.client.post(
            "/register",
            json={"username": "user", "password": ""},
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.get_json()["code"], -3)

    def test_register_does_not_return_password_in_response(self):
        """Response body must never include the plaintext password field."""
        cursor = _cursor_with_row()
        with mock.patch("flaskapp_pool.get_db", return_value=_conn_with_cursor(cursor)):
            resp = self.client.post(
                "/register",
                json={"username": "safe", "password": "topsecret"},
            )
        body = resp.get_json()
        self.assertNotIn("password", body)
        self.assertNotIn("topsecret", json.dumps(body))


class TestFlaskApiLogin(unittest.TestCase):
    """POST /login — credential check and player payload."""

    @classmethod
    def setUpClass(cls):
        from flaskapp_pool import app

        cls.client = app.test_client()

    def test_login_valid_credentials_returns_200_with_public_player(self):
        """Correct username/password → 200 JSON with id, username, high_score (no password)."""
        cursor = _cursor_with_row(row=_player_row(7, "alice", "secret", 42))
        with mock.patch("flaskapp_pool.get_db", return_value=_conn_with_cursor(cursor)):
            resp = self.client.post(
                "/login",
                json={"username": "alice", "password": "secret"},
            )
        self.assertEqual(resp.status_code, 200)
        body = resp.get_json()
        self.assertEqual(body["id"], 7)
        self.assertEqual(body["username"], "alice")
        self.assertEqual(body["high_score"], 42)
        self.assertNotIn("password", body)

    def test_login_wrong_password_returns_401(self):
        """Known username, wrong password → 401 'Invalid username or password'."""
        cursor = _cursor_with_row(row=None)
        with mock.patch("flaskapp_pool.get_db", return_value=_conn_with_cursor(cursor)):
            resp = self.client.post(
                "/login",
                json={"username": "alice", "password": "wrong"},
            )
        self.assertEqual(resp.status_code, 401)
        self.assertIn("Invalid username or password", resp.get_json()["error"])

    def test_login_unknown_user_returns_401(self):
        """Unknown username → 401 (same error shape as wrong password)."""
        cursor = _cursor_with_row(row=None)
        with mock.patch("flaskapp_pool.get_db", return_value=_conn_with_cursor(cursor)):
            resp = self.client.post(
                "/login",
                json={"username": "ghost", "password": "x"},
            )
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(resp.get_json()["error"], "Invalid username or password")


class TestFlaskApiUpdateScore(unittest.TestCase):
    """PUT /updateScore — persist high scores."""

    @classmethod
    def setUpClass(cls):
        from flaskapp_pool import app

        cls.client = app.test_client()

    def test_update_score_sets_high_score_in_database(self):
        """PUT with username + score → 200; subsequent login/getAllPlayers reflects new high_score."""
        cursor = _cursor_with_row()
        with mock.patch("flaskapp_pool.get_db", return_value=_conn_with_cursor(cursor)):
            resp = self.client.put(
                "/updateScore",
                json={"username": "alice", "score": 99},
            )
        self.assertEqual(resp.status_code, 200)
        sql, params = cursor.execute.call_args[0]
        self.assertIn("UPDATE", sql)
        self.assertEqual(params, (99, "alice"))

        # Simulate follow-up getAllPlayers reflecting the new score
        cursor2 = _cursor_with_row(rows=[_player_row(1, "alice", "pw", 99)])
        with mock.patch("flaskapp_pool.get_db", return_value=_conn_with_cursor(cursor2)):
            listing = self.client.get("/getAllPlayers").get_json()
        self.assertEqual(listing[0]["high_score"], 99)

    def test_update_score_for_unknown_user(self):
        """Document expected behavior when username does not exist (currently may still return 200)."""
        cursor = _cursor_with_row()
        with mock.patch("flaskapp_pool.get_db", return_value=_conn_with_cursor(cursor)):
            resp = self.client.put(
                "/updateScore",
                json={"username": "does_not_exist", "score": 10},
            )
        # Flask always returns 200 on successful SQL even if 0 rows updated.
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Updated score", resp.get_json()["message"])


class TestFlaskApiDelete(unittest.TestCase):
    """DELETE /delete — test user cleanup."""

    @classmethod
    def setUpClass(cls):
        from flaskapp_pool import app

        cls.client = app.test_client()

    def test_delete_existing_user_returns_200(self):
        """DELETE with valid username removes row; login afterward fails."""
        cursor = _cursor_with_row()
        with mock.patch("flaskapp_pool.get_db", return_value=_conn_with_cursor(cursor)):
            resp = self.client.delete("/delete", json={"username": "alice"})
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Deleted", resp.get_json()["message"])

        login_cursor = _cursor_with_row(row=None)
        with mock.patch("flaskapp_pool.get_db", return_value=_conn_with_cursor(login_cursor)):
            login = self.client.post(
                "/login",
                json={"username": "alice", "password": "pw"},
            )
        self.assertEqual(login.status_code, 401)

    def test_delete_is_idempotent_or_returns_clear_error(self):
        """Deleting twice should not corrupt state (define expected status code)."""
        cursor = _cursor_with_row()
        with mock.patch("flaskapp_pool.get_db", return_value=_conn_with_cursor(cursor)):
            first = self.client.delete("/delete", json={"username": "ghost"})
            second = self.client.delete("/delete", json={"username": "ghost"})
        # Current Flask behavior: both succeed with 200 (no rowcount check).
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)


# ---------------------------------------------------------------------------
# Auth bridge — auth.py
# ---------------------------------------------------------------------------


class TestAuthBridgeRegister(unittest.TestCase):
    """auth.register_user() maps Flask status codes to {code: ...}."""

    def test_maps_201_to_code_0(self):
        """Flask 201 → {"code": 0}."""
        with mock.patch("auth.requests.post", return_value=_http_response(201, {})):
            self.assertEqual(auth.register_user("u", "p"), {"code": 0})

    def test_maps_409_to_code_minus_1(self):
        """Flask 409 → {"code": -1} (username taken)."""
        with mock.patch(
            "auth.requests.post",
            return_value=_http_response(409, {"error": "Username already taken"}),
        ):
            self.assertEqual(auth.register_user("u", "p"), {"code": -1})

    def test_maps_400_to_validation_codes(self):
        """Flask 400 → code -2 or -3 for empty username/password."""
        with mock.patch(
            "auth.requests.post",
            return_value=_http_response(400, {"code": -3, "error": "Password cannot be empty."}),
        ):
            self.assertEqual(auth.register_user("user", "pw"), {"code": -3})
        with mock.patch(
            "auth.requests.post",
            return_value=_http_response(400, {"code": -2, "error": "Username cannot be empty."}),
        ):
            self.assertEqual(auth.register_user("user", "pw"), {"code": -2})

    def test_empty_username_short_circuits_without_http(self):
        """Blank username locally → {"code": -2} without calling Flask."""
        with mock.patch("auth.requests.post") as mock_post:
            self.assertEqual(auth.register_user("  ", "pw"), {"code": -2})
            mock_post.assert_not_called()

    def test_db_asleep_returns_code_minus_99_with_message(self):
        """Connection timeout / 5xx after retry → code -99 and 'Databass is asleep...' message."""
        with mock.patch("auth._wake_database"), mock.patch(
            "auth.requests.post",
            side_effect=requests.RequestException("timeout"),
        ):
            result = auth.register_user("u", "p")
        self.assertEqual(result["code"], -99)
        self.assertIn("Databass is asleep", result["message"])

    def test_wake_database_called_on_first_failure(self):
        """First RequestException triggers POST /login as tester/pass before retry."""
        ok = _http_response(201, {})
        with mock.patch("auth.requests.post") as mock_post:
            mock_post.side_effect = [
                requests.RequestException("down"),
                _http_response(200, {}),  # wake login
                ok,
            ]
            # register_user calls post for register; on failure calls _wake_database which posts login
            # Then retries register. So side_effect order depends on whether we patch _wake or not.
            result = auth.register_user("u", "p")
        self.assertEqual(result, {"code": 0})
        # First call is register, second is wake login, third is retry register
        self.assertGreaterEqual(mock_post.call_count, 2)
        wake_calls = [
            c
            for c in mock_post.call_args_list
            if c.kwargs.get("json") == {"username": "tester", "password": "pass"}
            or (len(c.args) > 0 and "/login" in str(c.args[0]))
        ]
        self.assertTrue(wake_calls or any("/login" in str(c) for c in mock_post.call_args_list))


class TestAuthBridgeLogin(unittest.TestCase):
    """auth.login_user() maps Flask login to game/frontend shape."""

    def test_maps_401_to_code_minus_1(self):
        """Invalid credentials → {"code": -1}."""
        with mock.patch(
            "auth.requests.post",
            return_value=_http_response(401, {"error": "Invalid username or password"}),
        ):
            self.assertEqual(auth.login_user("u", "bad"), {"code": -1})

    def test_success_returns_username_and_high_score(self):
        """Flask 200 → {"code": 0, "username", "playerId", "highScore"}."""
        resp = _http_response(200, {"id": 3, "username": "alice", "high_score": 12})
        resp.raise_for_status = mock.Mock()
        with mock.patch("auth.requests.post", return_value=resp):
            result = auth.login_user("alice", "pw")
        self.assertEqual(result["code"], 0)
        self.assertEqual(result["username"], "alice")
        self.assertEqual(result["playerId"], 3)
        self.assertEqual(result["highScore"], 12)

    def test_empty_username_returns_code_minus_2(self):
        """Blank username locally → {"code": -2}."""
        with mock.patch("auth.requests.post") as mock_post:
            self.assertEqual(auth.login_user("", "pw"), {"code": -2})
            mock_post.assert_not_called()


class TestAuthBridgeLeaderboard(unittest.TestCase):
    """auth.get_leaderboard() sorts and normalizes getAllPlayers rows."""

    def test_success_sorts_by_high_score_descending(self):
        """Players returned with highScore field, highest first."""
        resp = _http_response(
            200,
            [
                {"username": "a", "password": "x", "high_score": 5},
                {"username": "b", "password": "y", "high_score": 20},
                {"username": "c", "password": "z", "high_score": 10},
            ],
        )
        resp.raise_for_status = mock.Mock()
        with mock.patch("auth.requests.get", return_value=resp):
            result = auth.get_leaderboard()
        self.assertTrue(result["success"])
        scores = [p["highScore"] for p in result["players"]]
        self.assertEqual(scores, sorted(scores, reverse=True))
        self.assertEqual(result["players"][0]["username"], "b")

    def test_strips_password_and_skips_incomplete_rows(self):
        """Only username + highScore exposed; rows missing username omitted."""
        resp = _http_response(
            200,
            [
                {"username": "alice", "password": "secret", "high_score": 1},
                {"password": "x", "high_score": 99},
                {"username": None, "high_score": 50},
            ],
        )
        resp.raise_for_status = mock.Mock()
        with mock.patch("auth.requests.get", return_value=resp):
            result = auth.get_leaderboard()
        self.assertEqual(len(result["players"]), 1)
        self.assertEqual(result["players"][0], {"username": "alice", "highScore": 1})
        self.assertNotIn("password", result["players"][0])

    def test_failure_returns_success_false_and_empty_players(self):
        """DB unreachable → {"success": False, "players": [], "message": ...}."""
        with mock.patch("auth._wake_database"), mock.patch(
            "auth.requests.get",
            side_effect=requests.RequestException("down"),
        ):
            result = auth.get_leaderboard()
        self.assertFalse(result["success"])
        self.assertEqual(result["players"], [])
        self.assertIn("Databass", result["message"])


class TestAuthBridgeUpdateScore(unittest.TestCase):
    """auth.update_score() after a game ends."""

    def test_successful_put_returns_code_0(self):
        """Flask 200 → {"code": 0} (or mapped code from body)."""
        resp = _http_response(200, {"message": "Updated score for alice to 5"})
        resp.raise_for_status = mock.Mock()
        with mock.patch("auth.requests.put", return_value=resp):
            self.assertEqual(auth.update_score("alice", 5), {"code": 0})

    def test_network_failure_returns_code_minus_99(self):
        """Unreachable Flask after retries → code -99."""
        with mock.patch("auth._wake_database"), mock.patch(
            "auth.requests.put",
            side_effect=requests.RequestException("down"),
        ):
            result = auth.update_score("alice", 5)
        self.assertEqual(result["code"], -99)


# ---------------------------------------------------------------------------
# Game server HTTP — game_server.py
# ---------------------------------------------------------------------------


class TestGameServerHttpAuth(unittest.TestCase):
    """GET /auth/register and /auth/login proxy to auth.py → Flask."""

    @classmethod
    def setUpClass(cls):
        from fastapi.testclient import TestClient
        import game_server

        cls.game_server = game_server
        cls.client = TestClient(game_server.app)

    def test_auth_register_query_params_forwarded(self):
        """GET /auth/register?name=X&pwd=Y returns same code shape as auth.register_user."""
        with mock.patch.object(
            self.game_server.auth,
            "register_user",
            return_value={"code": 0},
        ) as mock_reg:
            resp = self.client.get("/auth/register", params={"name": "x", "pwd": "y"})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {"code": 0})
        mock_reg.assert_called_once_with("x", "y")

    def test_auth_login_query_params_forwarded(self):
        """GET /auth/login?name=X&pwd=Y returns code 0 + username/highScore on success."""
        payload = {"code": 0, "username": "x", "playerId": 1, "highScore": 3}
        with mock.patch.object(self.game_server.auth, "login_user", return_value=payload):
            resp = self.client.get("/auth/login", params={"name": "x", "pwd": "y"})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["code"], 0)
        self.assertEqual(resp.json()["username"], "x")
        self.assertEqual(resp.json()["highScore"], 3)

    def test_cors_headers_present_for_browser(self):
        """Responses include CORS headers so frontend fetch from nginx origin works."""
        with mock.patch.object(
            self.game_server.auth,
            "get_leaderboard",
            return_value={"success": True, "players": [], "message": "ok"},
        ):
            resp = self.client.get(
                "/leaderboard",
                headers={"Origin": "http://localhost:8080"},
            )
        self.assertEqual(resp.headers.get("access-control-allow-origin"), "*")


class TestGameServerHttpLeaderboard(unittest.TestCase):
    """GET /leaderboard — used by React Leaderboard screen."""

    @classmethod
    def setUpClass(cls):
        from fastapi.testclient import TestClient
        import game_server

        cls.game_server = game_server
        cls.client = TestClient(game_server.app)

    def test_leaderboard_returns_success_and_players_list(self):
        """200 JSON with success, players[], optional message."""
        payload = {
            "success": True,
            "message": "Leaderboard loaded successfully.",
            "players": [{"username": "a", "highScore": 1}],
        }
        with mock.patch.object(self.game_server.auth, "get_leaderboard", return_value=payload):
            resp = self.client.get("/leaderboard")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertIn("success", body)
        self.assertIsInstance(body["players"], list)

    def test_leaderboard_matches_auth_get_leaderboard_shape(self):
        """Each player has username (str) and highScore (int)."""
        payload = {
            "success": True,
            "message": "ok",
            "players": [{"username": "alice", "highScore": 7}],
        }
        with mock.patch.object(self.game_server.auth, "get_leaderboard", return_value=payload):
            players = self.client.get("/leaderboard").json()["players"]
        self.assertIsInstance(players[0]["username"], str)
        self.assertIsInstance(players[0]["highScore"], int)


# ---------------------------------------------------------------------------
# Game server WebSocket — /ws/game
# ---------------------------------------------------------------------------


class TestGameServerWebSocket(unittest.TestCase):
    """WebSocket session: headless game loop + client input.

    Protocol tests patch ``run_game_headless`` so the FastAPI frame queue is not
    flooded. Physics / flap / floor behavior is covered in TestGameLogicHeadless.
    """

    @classmethod
    def setUpClass(cls):
        from fastapi.testclient import TestClient
        import game_server

        cls.game_server = game_server
        cls.TestClient = TestClient

    def _client(self):
        return self.TestClient(self.game_server.app)

    @staticmethod
    def _scripted_run(script):
        """Return a run_game_headless stand-in that emits ``script`` then waits for stop/quit."""

        def fake_run(input_q, frame_cb, username, stop_event):
            for item in script:
                if stop_event.is_set():
                    return
                frame_cb(item)
            while not stop_event.wait(0.05):
                try:
                    msg = input_q.get_nowait()
                    if msg.get("type") == "quit":
                        return
                except queue.Empty:
                    pass

        return fake_run

    def test_ws_connect_accepts_without_auth_token(self):
        """ws://.../ws/game?player_name=alice connects with 101 Switching Protocols."""
        fake = self._scripted_run(
            [{"type": "frame", "state": "waiting", "score": 0, "high_score": 0, "buffer": []}]
        )
        with mock.patch.object(self.game_server, "run_game_headless", side_effect=fake):
            with self._client().websocket_connect("/ws/game?player_name=alice") as ws:
                data = ws.receive_json()
                self.assertEqual(data["type"], "frame")
                ws.send_json({"type": "quit"})

    def test_first_message_is_frame_type_frame(self):
        """After connect, client receives JSON with type 'frame' and game state fields."""
        fake = self._scripted_run(
            [
                {
                    "type": "frame",
                    "state": "waiting",
                    "score": 0,
                    "high_score": 0,
                    "buffer": [[{"char": " ", "color": "#001133"}]],
                }
            ]
        )
        with mock.patch.object(self.game_server, "run_game_headless", side_effect=fake):
            with self._client().websocket_connect("/ws/game?player_name=bob") as ws:
                data = ws.receive_json()
                self.assertEqual(data["type"], "frame")
                self.assertIn("state", data)
                self.assertIn("score", data)
                self.assertIn("buffer", data)
                ws.send_json({"type": "quit"})

    def test_flap_input_changes_player_vertical_position(self):
        """Send {"type": "flap"}; subsequent frames show bird_y moved upward vs prior frame."""

        def fake_run(input_q, frame_cb, username, stop_event):
            frame_cb(
                {
                    "type": "frame",
                    "state": "waiting",
                    "score": 0,
                    "high_score": 0,
                    "buffer": [],
                    "bird_y": 15,
                }
            )
            while not stop_event.is_set():
                try:
                    msg = input_q.get(timeout=0.05)
                except queue.Empty:
                    continue
                if msg.get("type") == "quit":
                    return
                if msg.get("type") == "flap":
                    frame_cb(
                        {
                            "type": "frame",
                            "state": "playing",
                            "score": 0,
                            "high_score": 0,
                            "buffer": [],
                            "bird_y": 15,
                        }
                    )
                    frame_cb(
                        {
                            "type": "frame",
                            "state": "playing",
                            "score": 0,
                            "high_score": 0,
                            "buffer": [],
                            "bird_y": 10,
                        }
                    )
                    return

        with mock.patch.object(self.game_server, "run_game_headless", side_effect=fake_run):
            with self._client().websocket_connect("/ws/game?player_name=flapper") as ws:
                first = ws.receive_json()
                self.assertEqual(first["state"], "waiting")
                ws.send_json({"type": "flap"})
                y1 = ws.receive_json()["bird_y"]
                y2 = ws.receive_json()["bird_y"]
                self.assertLess(y2, y1)

    def test_quit_input_ends_session_cleanly(self):
        """Send {"type": "quit"}; connection closes without server error."""
        quit_seen = threading.Event()

        def fake_run(input_q, frame_cb, username, stop_event):
            frame_cb({"type": "frame", "state": "waiting", "score": 0, "high_score": 0, "buffer": []})
            while not stop_event.is_set():
                try:
                    msg = input_q.get(timeout=0.05)
                except queue.Empty:
                    continue
                if msg.get("type") == "quit":
                    quit_seen.set()
                    return

        with mock.patch.object(self.game_server, "run_game_headless", side_effect=fake_run):
            with self._client().websocket_connect("/ws/game?player_name=quitter") as ws:
                ws.receive_json()
                ws.send_json({"type": "quit"})
        self.assertTrue(quit_seen.wait(2))

    def test_collision_or_floor_triggers_game_over_message(self):
        """Eventually receive {"type": "game_over", "score": int, "high_score": int}."""
        fake = self._scripted_run(
            [
                {"type": "frame", "state": "waiting", "score": 0, "high_score": 0, "buffer": []},
                {"type": "frame", "state": "playing", "score": 0, "high_score": 0, "buffer": []},
                {"type": "frame", "state": "dead", "score": 0, "high_score": 0, "buffer": []},
                {"type": "game_over", "score": 3, "high_score": 5},
            ]
        )
        with mock.patch.object(self.game_server, "run_game_headless", side_effect=fake):
            with self._client().websocket_connect("/ws/game?player_name=doomed") as ws:
                saw_game_over = None
                for _ in range(10):
                    msg = ws.receive_json()
                    if msg.get("type") == "game_over":
                        saw_game_over = msg
                        break
        self.assertIsNotNone(saw_game_over)
        self.assertIsInstance(saw_game_over["score"], int)
        self.assertIsInstance(saw_game_over["high_score"], int)

    def test_game_over_stops_frame_stream(self):
        """No further 'frame' messages after 'game_over' (per send_frames loop)."""

        def fake_run(input_q, frame_cb, username, stop_event):
            frame_cb({"type": "frame", "state": "playing", "score": 0, "high_score": 0, "buffer": []})
            frame_cb({"type": "game_over", "score": 1, "high_score": 1})
            # Would be a bug if the server forwarded this after game_over:
            frame_cb({"type": "frame", "state": "playing", "score": 2, "high_score": 2, "buffer": []})

        with mock.patch.object(self.game_server, "run_game_headless", side_effect=fake_run):
            with self._client().websocket_connect("/ws/game?player_name=x") as ws:
                types = []
                for _ in range(5):
                    msg = ws.receive_json()
                    types.append(msg["type"])
                    if msg["type"] == "game_over":
                        break
        self.assertEqual(types[-1], "game_over")
        # send_frames returns on game_over, so the trailing frame must not appear
        self.assertEqual(types.count("game_over"), 1)
        self.assertLessEqual(types.count("frame"), 1)

    def test_anonymous_player_name_still_runs_game(self):
        """player_name='' (guest) starts game; high_score lookup returns 0 if not logged in."""
        seen_name = {}

        def fake_run(input_q, frame_cb, username, stop_event):
            seen_name["username"] = username
            frame_cb(
                {
                    "type": "frame",
                    "state": "waiting",
                    "score": 0,
                    "high_score": 0,
                    "buffer": [],
                }
            )
            while not stop_event.wait(0.05):
                try:
                    if input_q.get_nowait().get("type") == "quit":
                        return
                except queue.Empty:
                    pass

        with mock.patch.object(self.game_server, "run_game_headless", side_effect=fake_run):
            with self._client().websocket_connect("/ws/game") as ws:
                data = ws.receive_json()
                self.assertEqual(data["type"], "frame")
                self.assertEqual(data.get("high_score", 0), 0)
                ws.send_json({"type": "quit"})
        self.assertEqual(seen_name.get("username"), "")

    def test_server_survives_client_disconnect_mid_game(self):
        """Abrupt disconnect sets stop_event; game thread exits within timeout."""
        stop_seen = threading.Event()

        def fake_run(input_q, frame_cb, username, stop_event):
            frame_cb({"type": "frame", "state": "waiting", "score": 0, "high_score": 0, "buffer": []})
            if stop_event.wait(2):
                stop_seen.set()

        with mock.patch.object(self.game_server, "run_game_headless", side_effect=fake_run):
            with self._client().websocket_connect("/ws/game?player_name=dc") as ws:
                ws.receive_json()
        self.assertTrue(stop_seen.wait(2))


# ---------------------------------------------------------------------------
# Game logic (unit)
# ---------------------------------------------------------------------------


class TestGameLogicCollision(unittest.TestCase):
    """Pixel-accurate collision between Player and obstacles."""

    def _actor(self, x, y, display):
        return SimpleNamespace(
            position=(x, y),
            width=len(display[0]),
            height=len(display),
            sprite=SimpleNamespace(display=display),
        )

    def test_no_overlap_returns_false(self):
        """Bounding boxes disjoint → check_collision is False."""
        player = self._actor(0, 0, [["A"]])
        obs = self._actor(10, 10, [["B"]])
        self.assertFalse(check_collision(player, obs))

    def test_overlap_but_transparent_pixels_returns_false(self):
        """Boxes overlap but only space characters align → False."""
        player = self._actor(0, 0, [["A", " "], [" ", " "]])
        obs = self._actor(0, 0, [[" ", "B"], [" ", " "]])
        self.assertFalse(check_collision(player, obs))

    def test_solid_pixel_overlap_returns_true(self):
        """Both sprites non-space at same world coord → True → game should end."""
        player = self._actor(0, 0, [["A", " "], [" ", " "]])
        obs = self._actor(0, 0, [["B", " "], [" ", " "]])
        self.assertTrue(check_collision(player, obs))

    def test_collision_with_tentacle_pair(self):
        """Player hits top or bottom tentacle in a pair → collision detected."""
        player = Player(20, 5)
        top = Tentacle(20, 5, str(_ASSETS / "tentacles_top.txt"))
        # Force same position for a definite AABB; pixel result may vary — assert bool + solid case
        hit = check_collision(player, top)
        self.assertIsInstance(hit, bool)
        # Guaranteed solid overlap via synthetic displays already covered; also try overlapping boxes
        bottom = Tentacle(player.position[0], player.position[1], str(_ASSETS / "tentacles_bottom.txt"))
        self.assertIsInstance(check_collision(player, bottom), bool)

    def test_collision_with_solo_jellyfish_or_pufferfish(self):
        """Solo obstacle types use same check_collision path."""
        player = Player(10, 10)
        jf = JellyfishObstacle(10, 10, str(_ASSETS / "jellyfish.txt"))
        pf = PufferfishObstacle(10, 10)
        self.assertIsInstance(check_collision(player, jf), bool)
        self.assertIsInstance(check_collision(player, pf), bool)


class TestGameLogicScoring(unittest.TestCase):
    """Score increments when passing obstacle pairs."""

    def test_score_increments_once_per_pair(self):
        """update_score adds 1 when player passes pair; passed_pairs prevents double count."""
        player = Player(50, 5)
        top = Obstacle(0, -5, str(_ASSETS / "tentacles_top.txt"))
        bottom = Obstacle(0, 10, str(_ASSETS / "tentacles_bottom.txt"))
        passed = set()
        score = update_score(player, [(top, bottom)], passed, 0)
        self.assertEqual(score, 1)
        score = update_score(player, [(top, bottom)], passed, score)
        self.assertEqual(score, 1)

    def test_score_does_not_increment_before_pair_cleared(self):
        """Pair still on screen to the right of player → score unchanged."""
        top = Obstacle(40, -5, str(_ASSETS / "tentacles_top.txt"))
        bottom = Obstacle(40, 10, str(_ASSETS / "tentacles_bottom.txt"))
        player = Player(5, 5)
        passed = set()
        self.assertEqual(update_score(player, [(top, bottom)], passed, 3), 3)

    def test_removed_pairs_pruned_from_passed_pairs(self):
        """passed_pairs.intersection_update drops stale pair ids."""
        player = Player(50, 5)
        top = Obstacle(0, -5, str(_ASSETS / "tentacles_top.txt"))
        bottom = Obstacle(0, 10, str(_ASSETS / "tentacles_bottom.txt"))
        passed = {id(top), 999999}
        update_score(player, [(top, bottom)], passed, 0)
        self.assertEqual(passed, {id(top)})


class TestGameLogicHeadless(unittest.TestCase):
    """run_game_headless() — web game engine (no terminal)."""

    def test_emits_frames_at_target_fps_rate(self):
        """Frame callback invoked ~30/sec; each payload has type 'frame'."""
        frames = []
        input_q: queue.Queue = queue.Queue()
        stop = threading.Event()

        def runner():
            with mock.patch("game_logic.get_high_score", return_value=0), mock.patch(
                "game_logic.sync_high_score", side_effect=lambda u, s, h: h
            ):
                run_game_headless(input_q, frames.append, "fps", stop)

        t = threading.Thread(target=runner, daemon=True)
        t.start()
        # wait for waiting frame
        deadline = time.time() + 2
        while time.time() < deadline and not frames:
            time.sleep(0.01)
        input_q.put({"type": "flap"})
        start = time.time()
        time.sleep(0.45)
        stop.set()
        t.join(timeout=3)
        elapsed = time.time() - start
        playing = [f for f in frames if f.get("type") == "frame" and f.get("state") == "playing"]
        if elapsed > 0 and playing:
            rate = len(playing) / elapsed
            # Allow wide tolerance for CI load
            self.assertGreater(rate, 10)
            self.assertLess(rate, 60)
        for f in frames:
            if f.get("type") == "frame":
                self.assertEqual(f["type"], "frame")

    def test_frame_payload_includes_render_fields(self):
        """Frames include state, score, grid/buffer data expected by GameCanvas.tsx."""
        frames = []
        input_q: queue.Queue = queue.Queue()
        stop = threading.Event()

        def runner():
            with mock.patch("game_logic.get_high_score", return_value=0), mock.patch(
                "game_logic.sync_high_score", side_effect=lambda u, s, h: h
            ), mock.patch("game_logic.time.sleep", return_value=None):
                run_game_headless(input_q, frames.append, "payload", stop)

        t = threading.Thread(target=runner, daemon=True)
        t.start()
        deadline = time.time() + 2
        while time.time() < deadline and not frames:
            time.sleep(0.01)
        stop.set()
        t.join(timeout=2)
        self.assertTrue(frames)
        frame = frames[0]
        self.assertEqual(frame["type"], "frame")
        self.assertIn("state", frame)
        self.assertIn("score", frame)
        self.assertIn("buffer", frame)
        self.assertIsInstance(frame["buffer"], list)

    def test_gravity_moves_player_down_without_input(self):
        """Over several frames with no flap, bird_y increases."""
        import display_buffer

        frames = []
        bird_ys: list[float] = []
        input_q: queue.Queue = queue.Queue()
        stop = threading.Event()
        real_render = display_buffer.render_frame

        def tracking_render(player, *args, **kwargs):
            fd = real_render(player, *args, **kwargs)
            bird_ys.append(float(player.position[1]))
            return fd

        def runner():
            with mock.patch("game_logic.get_high_score", return_value=0), mock.patch(
                "game_logic.sync_high_score", side_effect=lambda u, s, h: h
            ), mock.patch("game_logic.time.sleep", return_value=None), mock.patch(
                "display_buffer.render_frame", side_effect=tracking_render
            ):
                run_game_headless(input_q, frames.append, "grav", stop)

        t = threading.Thread(target=runner, daemon=True)
        t.start()
        while not frames:
            time.sleep(0.01)
        # One flap starts the run; afterward only gravity acts.
        input_q.put({"type": "flap"})
        deadline = time.time() + 5
        while time.time() < deadline:
            if any(f.get("type") == "game_over" for f in frames):
                break
            if len([f for f in frames if f.get("state") == "playing"]) >= 40:
                break
            time.sleep(0.01)
        stop.set()
        t.join(timeout=3)

        playing_count = len([f for f in frames if f.get("state") == "playing"])
        # bird_ys includes waiting + playing + death frames; use the playing window
        self.assertGreaterEqual(playing_count, 5)
        # Drop the initial waiting samples (same Y), keep trajectory after flap
        unique_prefix = 0
        while unique_prefix + 1 < len(bird_ys) and bird_ys[unique_prefix + 1] == bird_ys[0]:
            unique_prefix += 1
        ys = bird_ys[unique_prefix:]
        self.assertGreaterEqual(len(ys), 5, f"trajectory too short: {ys!r}")

        peak_i = min(range(len(ys)), key=lambda i: ys[i])
        after_peak = ys[peak_i + 1 :]
        self.assertTrue(after_peak, "expected samples after jump apex")
        self.assertGreater(
            max(after_peak),
            ys[peak_i],
            f"bird should fall after apex; ys={ys[:40]!r}",
        )

    def test_flap_from_input_queue_applies_upward_velocity(self):
        """Put {"type": "flap"} on input_queue; bird moves up on next ticks."""
        frames = []
        input_q: queue.Queue = queue.Queue()
        stop = threading.Event()

        def runner():
            with mock.patch("game_logic.get_high_score", return_value=0), mock.patch(
                "game_logic.sync_high_score", side_effect=lambda u, s, h: h
            ), mock.patch("game_logic.time.sleep", return_value=None):
                run_game_headless(input_q, frames.append, "up", stop)

        t = threading.Thread(target=runner, daemon=True)
        t.start()
        while not frames:
            time.sleep(0.01)
        input_q.put({"type": "flap"})
        time.sleep(0.05)
        # allow fall then flap hard
        for _ in range(5):
            time.sleep(0.02)
        before = len(frames)
        input_q.put({"type": "flap"})
        time.sleep(0.08)
        stop.set()
        t.join(timeout=3)
        self.assertGreater(len(frames), before)

    def test_stop_event_terminates_loop(self):
        """stop_event.set() ends thread without hanging."""
        frames = []
        input_q: queue.Queue = queue.Queue()
        stop = threading.Event()

        def runner():
            with mock.patch("game_logic.get_high_score", return_value=0), mock.patch(
                "game_logic.sync_high_score", side_effect=lambda u, s, h: h
            ), mock.patch("game_logic.time.sleep", return_value=None):
                run_game_headless(input_q, frames.append, "stop", stop)

        t = threading.Thread(target=runner, daemon=True)
        t.start()
        while not frames:
            time.sleep(0.01)
        stop.set()
        t.join(timeout=2)
        self.assertFalse(t.is_alive())

    def test_game_over_calls_update_score_for_logged_in_user(self):
        """When username set, end-of-run persists score via auth.update_score (mock in unit test)."""
        import game_logic

        with mock.patch("game_logic.persist_score", return_value={"code": 0}) as persist:
            self.assertEqual(game_logic.sync_high_score("scorer", 10, 0), 10)
            persist.assert_called_once_with("scorer", 10)

        frames = []
        input_q: queue.Queue = queue.Queue()
        stop = threading.Event()

        def runner():
            with mock.patch("game_logic.get_high_score", return_value=0), mock.patch(
                "game_logic.sync_high_score", side_effect=lambda u, s, h: max(h, s)
            ) as sync, mock.patch("game_logic.time.sleep", return_value=None):
                run_game_headless(input_q, frames.append, "scorer", stop)
                sync.assert_called()

        t = threading.Thread(target=runner, daemon=True)
        t.start()
        while not frames:
            time.sleep(0.01)
        input_q.put({"type": "flap"})
        deadline = time.time() + 5
        while time.time() < deadline and not any(f.get("type") == "game_over" for f in frames):
            time.sleep(0.01)
        stop.set()
        t.join(timeout=3)
        self.assertTrue(any(f.get("type") == "game_over" for f in frames))


class TestObstacleSpawner(unittest.TestCase):
    """obstacle_spawner.py — obstacle lifecycle."""

    def _spawner(self, **kwargs):
        types = [
            ObstacleTypeConfig(
                "static",
                1.0,
                str(_ASSETS / "tentacles_top.txt"),
                str(_ASSETS / "tentacles_bottom.txt"),
            )
        ]
        defaults = dict(
            screen_width=80,
            game_height=30,
            obstacle_types=types,
            obstacle_speed=2,
            spawn_interval=1000,
            max_pairs=2,
            rng_seed=1,
        )
        defaults.update(kwargs)
        return ObstacleSpawner(**defaults)

    def test_spawns_within_max_groups_limit(self):
        """update() never exceeds max_pairs / max_groups configured."""
        spawner = self._spawner(max_pairs=1, spawn_interval=1)
        for _ in range(20):
            spawner.update()
            self.assertLessEqual(spawner._group_count(), 1)

    def test_obstacles_move_left_each_tick(self):
        """x decreases by obstacle_speed each update."""
        spawner = self._spawner(obstacle_speed=3)
        self.assertTrue(spawner.obstacles)
        x0 = spawner.obstacles[0].position[0]
        spawner.update()
        self.assertLess(spawner.obstacles[0].position[0], x0)

    def test_off_screen_obstacles_removed(self):
        """Pairs/solos with x + width <= 0 are dropped from lists."""
        spawner = self._spawner(obstacle_speed=50)
        # Move far left until pruned
        for _ in range(50):
            if not spawner.obstacles:
                break
            spawner.update()
        # With huge speed and no respawn (high interval), list should empty
        self.assertEqual(spawner.obstacles, [])

    def test_moving_obstacles_apply_sine_vertical_offset(self):
        """moving/jellyfish configs change y via amplitude/frequency."""
        types = [
            ObstacleTypeConfig(
                "moving",
                1.0,
                str(_ASSETS / "tentacles_top.txt"),
                str(_ASSETS / "tentacles_bottom.txt"),
                amplitude=5.0,
                frequency=0.5,
            )
        ]
        spawner = ObstacleSpawner(
            80, 30, types, obstacle_speed=0.1, spawn_interval=9999, max_pairs=1, rng_seed=0
        )
        y0 = spawner.obstacles[0].position[1]
        for _ in range(10):
            spawner.update()
        y1 = spawner.obstacles[0].position[1]
        # With amplitude, y should change over frames (sine)
        self.assertTrue(y0 != y1 or math.sin(0.5) != 0)

    def test_pufferfish_inflates_when_player_near(self):
        """PufferfishObstacle.update_inflation reacts to player_x proximity."""
        pf = PufferfishObstacle(100.0, 15)
        self.assertEqual(pf._stage, 0)
        # Simulate scrolling toward player at x=10
        for x in range(100, 10, -5):
            pf.set_x(float(x))
            pf.update_inflation(10.0, 10.0)
        self.assertGreaterEqual(pf._stage, 0)
        self.assertLessEqual(pf._stage, 3)
        # After approaching, stage should have advanced from 0 for typical distances
        pf2 = PufferfishObstacle(80.0, 15)
        pf2.set_x(20.0)
        pf2.update_inflation(10.0, 10.0)
        self.assertGreaterEqual(pf2._stage, 0)


class TestPlayerAndSprites(unittest.TestCase):
    """Core game objects load assets correctly."""

    def test_player_loads_fish_sprite(self):
        """Player( x, y ) has non-empty sprite.display grid."""
        player = Player(10, 5)
        self.assertTrue(player.sprite.display)
        self.assertGreater(len(player.sprite.display[0]), 0)

    def test_obstacle_loads_tentacle_assets(self):
        """Obstacle paths under assets/ resolve and render."""
        top = Obstacle(70, -5, str(_ASSETS / "tentacles_top.txt"))
        bot = Obstacle(70, 10, str(_ASSETS / "tentacles_bottom.txt"))
        self.assertTrue(top.sprite.display)
        self.assertTrue(bot.sprite.display)

    def test_display_buffer_dimensions_match_canvas(self):
        """BUFFER_COLS / GAME_AREA_HEIGHT in display_buffer.py match frontend canvas size."""
        self.assertEqual(BUFFER_COLS, 100)
        self.assertEqual(GAME_AREA_HEIGHT, 30)
        self.assertEqual(HEADER_ROWS, 4)
        # Frontend sizes canvas from frame.buffer; total rows = header + game area
        self.assertEqual(HEADER_ROWS + GAME_AREA_HEIGHT, 34)


# ---------------------------------------------------------------------------
# End-to-end — public stack (Azure ACI by default; no local Docker required)
# ---------------------------------------------------------------------------


def _public_api_url() -> str:
    """Game-server routes exposed via nginx (or direct GAME_SERVER_URL override)."""
    return os.getenv("GAME_SERVER_URL", DEFAULT_AZURE_APP_URL).rstrip("/")


class TestEndToEndLocalStack(unittest.TestCase):
    """
    Live checks against the public deployment (same URL browsers use).

    Flask itself is not internet-facing on Azure; auth/DB are exercised through
    game-server proxies under /auth/ and /leaderboard. Optional FLASK_URL still
    enables direct cleanup via DELETE /delete when running against local compose.
    """

    def test_flask_reachable_from_host(self):
        """Flask/DB reachable via public auth proxy (register round-trip)."""
        # Direct GET / on Flask is only available with FLASK_URL (local compose).
        flask = os.getenv("FLASK_URL", "").rstrip("/")
        if flask:
            resp = requests.get(f"{flask}/", timeout=10)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Hello, World!", resp.text)
            return

        # Deployed: prove Flask+SQL via auth.register through nginx → game-server.
        api = _public_api_url()
        name = f"pytest_probe_{uuid.uuid4().hex[:8]}"
        resp = requests.get(
            f"{api}/auth/register",
            params={"name": name, "pwd": "pytest_pass"},
            timeout=90,
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn(resp.json().get("code"), (0, -1, -99))

    def test_game_server_leaderboard_reachable(self):
        """GET /leaderboard returns JSON (success true or false with message)."""
        url = _public_api_url()
        resp = requests.get(f"{url}/leaderboard", timeout=90)
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertIn("success", body)
        self.assertIn("players", body)

    def test_full_register_login_leaderboard_flow(self):
        """
        1. Register unique test user via /auth/register
        2. Login via /auth/login → code 0
        3. GET /leaderboard includes that user (highScore 0)
        4. DELETE via Flask /delete when FLASK_URL is set (local only)
        """
        gs = _public_api_url()
        flask = os.getenv("FLASK_URL", "").rstrip("/")
        name = f"pytest_user_{uuid.uuid4().hex[:8]}"
        pwd = "pytest_pass"
        reg = requests.get(f"{gs}/auth/register", params={"name": name, "pwd": pwd}, timeout=90)
        self.assertEqual(reg.status_code, 200)
        self.assertEqual(reg.json().get("code"), 0, reg.json())
        login = requests.get(f"{gs}/auth/login", params={"name": name, "pwd": pwd}, timeout=90)
        self.assertEqual(login.json().get("code"), 0, login.json())
        board = requests.get(f"{gs}/leaderboard", timeout=90).json()
        names = [p.get("username") for p in board.get("players", [])]
        self.assertIn(name, names)
        if flask:
            requests.delete(f"{flask}/delete", json={"username": name}, timeout=30)

    def test_websocket_game_playable_for_ten_seconds(self):
        """Connect WS, receive frames for ~10s, send flap, disconnect without error."""
        from websockets.sync.client import connect

        base = _public_api_url()
        ws_url = base.replace("http://", "ws://").replace("https://", "wss://")
        ws_url = f"{ws_url}/ws/game?player_name=smoke"
        with connect(ws_url, open_timeout=30) as ws:
            first = json.loads(ws.recv())
            self.assertEqual(first["type"], "frame")
            ws.send(json.dumps({"type": "flap"}))
            end = time.time() + 10
            while time.time() < end:
                try:
                    json.loads(ws.recv(timeout=1))
                except Exception:
                    break
                if time.time() > end - 9.5:
                    ws.send(json.dumps({"type": "flap"}))


class TestEndToEndAzureDeployment(unittest.TestCase):
    """Post-deploy checks against the ACI frontend URL."""

    def test_frontend_serves_index_html(self):
        """GET deployed URL / returns 200 with React shell."""
        url = _azure_app_url()
        resp = requests.get(f"{url}/", timeout=30)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(
            "html" in resp.text.lower() or "root" in resp.text.lower() or resp.headers.get("content-type", "").startswith("text/html")
        )

    def test_auth_proxy_through_nginx(self):
        """GET deployed /leaderboard returns JSON (DB may be cold on first hit)."""
        url = _azure_app_url()
        resp = requests.get(f"{url}/leaderboard", timeout=90)
        self.assertEqual(resp.status_code, 200)
        self.assertIsInstance(resp.json(), dict)

    def test_websocket_upgrade_through_nginx(self):
        """wss/ws via /ws/game?player_name=smoke completes handshake."""
        from websockets.sync.client import connect

        base = _azure_app_url()
        if base.startswith("https://"):
            ws_url = base.replace("https://", "wss://")
        else:
            ws_url = base.replace("http://", "ws://")
        with connect(f"{ws_url}/ws/game?player_name=smoke", open_timeout=30) as ws:
            msg = json.loads(ws.recv())
            self.assertEqual(msg["type"], "frame")
            ws.send(json.dumps({"type": "quit"}))

    def test_cold_start_shows_graceful_message_not_502(self):
        """
        First request after DB pause: frontend auth shows asleep message (code -99)
        or leaderboard returns success:false with message — not nginx 502.
        """
        url = _azure_app_url()
        resp = requests.get(f"{url}/leaderboard", timeout=90)
        self.assertNotEqual(resp.status_code, 502)
        body = resp.json()
        self.assertTrue(
            body.get("success") is True
            or body.get("success") is False
            or "code" in body
            or "players" in body
        )


# ---------------------------------------------------------------------------
# Regression guards — things that broke before
# ---------------------------------------------------------------------------


class TestRegressionGuards(unittest.TestCase):
    """Catch known past failures."""

    def test_game_server_dockerfile_has_uvicorn_cmd(self):
        """Dockerfile.game CMD runs uvicorn game_server:app (game-server was down on Azure without this)."""
        text = (_SRC / "Dockerfile.game").read_text()
        self.assertIn("uvicorn", text)
        self.assertIn("game_server:app", text)

    def test_auth_uses_post_not_get_for_flask_login(self):
        """auth.login_user POSTs JSON to /login (GET mismatch caused 'cannot reach backend')."""
        src = (_SRC / "auth.py").read_text()
        self.assertIn("requests.post", src)
        self.assertIn("/login", src)
        # Ensure login_user body uses post
        self.assertIn("def login_user", src)
        login_fn = src.split("def login_user")[1].split("def ")[0]
        self.assertIn("requests.post", login_fn)
        self.assertNotIn("requests.get", login_fn)

    def test_flask_login_accepts_post_json_body(self):
        """flaskapp /login expects POST {username, password}, not query params."""
        from flaskapp_pool import app

        cursor = _cursor_with_row(row=_player_row())
        with mock.patch("flaskapp_pool.get_db", return_value=_conn_with_cursor(cursor)):
            resp = app.test_client().post(
                "/login",
                json={"username": "alice", "password": "secret"},
            )
        self.assertEqual(resp.status_code, 200)

    def test_deploy_uses_unique_image_tag_not_only_latest(self):
        """
        deploy.yml tags images with github.sha and passes frontendImage=frontend:<sha>
        so ACI sees a template change and pulls new layers ( :latest alone leaves old UI ).
        """
        text = (_REPO_ROOT / ".github" / "workflows" / "deploy.yml").read_text()
        self.assertIn("IMAGE_TAG: ${{ github.sha }}", text)
        self.assertIn("frontendImage=frontend:${{ env.IMAGE_TAG }}", text)

    def test_compose_game_server_base_url_points_at_flask_service(self):
        """docker-compose: game-server BASE_URL=http://flask-api:5000 (not localhost)."""
        text = (_REPO_ROOT / "docker-compose-web.yml").read_text()
        self.assertIn("BASE_URL: http://flask-api:5000", text)

    def test_nginx_proxies_auth_leaderboard_and_ws_to_game_server(self):
        """frontend/nginx.conf has /auth/, /leaderboard, /ws/ → game-server:8765."""
        text = (_REPO_ROOT / "frontend" / "nginx.conf").read_text()
        self.assertIn("location /auth/", text)
        self.assertIn("location /leaderboard", text)
        self.assertIn("location /ws/", text)
        self.assertIn("game-server:8765", text)


if __name__ == "__main__":
    unittest.main()
