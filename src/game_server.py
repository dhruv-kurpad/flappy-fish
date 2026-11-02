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

import logging
import math
import time

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

import auth
from game_logic import run_game_headless

logger = logging.getLogger(__name__)


def client_ip(request: Request) -> str:
    """Real client IP. Behind Vercel's proxy request.client is the proxy, so
    prefer the first X-Forwarded-For entry, then X-Real-IP."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()
    return request.client.host if request.client else "unknown"


# In-memory storage: counters are per serverless instance (best-effort on Vercel).
limiter = Limiter(key_func=client_ip)

app = FastAPI()
app.state.limiter = limiter


def _on_rate_limited(request: Request, exc: RateLimitExceeded):
    logger.warning("Rate limit hit: %s %s (%s)", client_ip(request), request.url.path, exc.detail)
    response = _rate_limit_exceeded_handler(request, exc)
    # slowapi only adds headers when headers_enabled=True, which would require a
    # `response` param on every route, so set Retry-After here instead.
    retry_after = 60
    try:
        item, args = request.state.view_rate_limit
        reset_time, _remaining = limiter.limiter.get_window_stats(item, *args)
        retry_after = max(1, math.ceil(reset_time - time.time()))
    except Exception:
        pass
    response.headers["Retry-After"] = str(retry_after)
    return response


app.add_exception_handler(RateLimitExceeded, _on_rate_limited)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Auth / leaderboard HTTP endpoints (via auth.py → flaskapp.py) ---
# Limits are per client IP within a rolling window. /ws/game is not covered
# (slowapi does not support WebSockets).

@app.get("/auth/register")
@limiter.limit("5/minute")
def register(request: Request, name: str = Query(...), pwd: str = Query(...)):
    return auth.register_user(name, pwd)


@app.get("/auth/login")
@limiter.limit("10/minute")
def login(request: Request, name: str = Query(...), pwd: str = Query(...)):
    return auth.login_user(name, pwd)


@app.get("/leaderboard")
@limiter.limit("60/minute")
def leaderboard(request: Request):
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
