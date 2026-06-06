"""
FastAPI server: HTTP auth proxy + WebSocket game sessions.

Start with:
    cd src && uvicorn game_server:app --reload --port 8765
"""

import asyncio
import queue
import sys
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware

import auth
from game_logic import run_game_headless

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Auth / leaderboard HTTP endpoints (via auth.py → flaskapp.py) ---

@app.get("/auth/register")
def register(name: str = Query(...), pwd: str = Query(...)):
    return auth.register_user(name, pwd)


@app.get("/auth/login")
def login(name: str = Query(...), pwd: str = Query(...)):
    return auth.login_user(name, pwd)


@app.get("/leaderboard")
def leaderboard():
    return auth.get_leaderboard()


# --- WebSocket game endpoint ---

@app.websocket("/ws/game")
async def game_ws(
    websocket: WebSocket,
    player_name: str = Query(default=""),
):
    await websocket.accept()

    input_q: queue.Queue = queue.Queue()
    frame_q: asyncio.Queue = asyncio.Queue(maxsize=4)
    stop_event = threading.Event()
    loop = asyncio.get_event_loop()

    def frame_callback(frame_data: dict) -> None:
        # Called from the game thread; push to the async queue safely.
        try:
            loop.call_soon_threadsafe(frame_q.put_nowait, frame_data)
        except asyncio.QueueFull:
            pass  # drop the frame if the client is too slow

    def run_game() -> None:
        try:
            run_game_headless(input_q, frame_callback, player_name, stop_event)
        except Exception as exc:
            loop.call_soon_threadsafe(
                frame_q.put_nowait,
                {"type": "error", "message": str(exc)},
            )

    game_thread = threading.Thread(target=run_game, daemon=True)
    game_thread.start()

    async def send_frames() -> None:
        while True:
            frame = await frame_q.get()
            try:
                await websocket.send_json(frame)
            except Exception:
                return
            # Stop sending once game_over has been delivered.
            if frame.get("type") == "game_over":
                return

    async def receive_input() -> None:
        while True:
            try:
                data = await websocket.receive_json()
                input_q.put(data)
            except WebSocketDisconnect:
                return
            except Exception:
                return

    try:
        await asyncio.gather(send_frames(), receive_input())
    except Exception:
        pass
    finally:
        stop_event.set()
        game_thread.join(timeout=2)
