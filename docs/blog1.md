> **Part 1 of 3 · Full-Stack Learning Series**

# From Terminal to Browser

*I had a working Python game. I used it as a vehicle to learn React, WebSockets, Docker, and what full-stack development actually feels like outside a tutorial.*

**Stack:** Python · FastAPI · Flask · WebSockets · React · Azure SQL · Docker · Azure Container Instances

---

I had a Flappy Bird-style terminal game — accounts, leaderboard, real-time input, roughly a thousand lines in `game_logic.py`. Rather than rewrite it, I set one constraint: keep the Python engine, build a browser interface around it. A working engine meant I could focus on the parts I wanted to do: how a frontend talks to a backend, how services are split, and what it actually takes to ship something.

## Choosing a protocol

I tested REST polling before ruling it out. Even at 100–150ms intervals the game felt choppy — that was worth discovering hands-on. Real-time gameplay needs continuous updates, not periodic snapshots.

| Approach | Latency | Trade-off | Learning value |
| --- | --- | --- | --- |
| Rewrite in JS | ✅ Low | Two codebases to maintain | React only — no cross-language communication |
| REST polling | ❌ Visible jitter | Simple to implement | REST APIs, but not real-time protocols |
| **WebSockets** ✅ | ✅ ~30fps | One engine, persistent connection | Full stack: protocols, service design, React, Docker |

The solution was adding `run_game_headless()` to the existing engine — same game loop, each frame serialized as JSON instead of printed to the terminal. React draws the grid and sends back `{"type": "flap"}`. Neither side knows anything about the other's internals.

```python
# game_logic.py — headless frame payload (simplified)
def run_game_headless(input_queue, frame_callback, username, stop_event):
    fd = render_frame(player, obstacles, score, high_score, ...)
    frame_callback({
        "type": "frame",
        "state": "playing",
        "buffer": fd["buffer"],  # 2D grid of {char, color}
        "score": score,
        "high_score": high_score,
    })
    # On death → {"type": "game_over", "score": ..., "high_score": ...}
```

## FastAPI and Flask — a deliberate split

The app had two distinct jobs: stream game frames in real time, and handle REST calls for login and leaderboards against Azure SQL. I researched both frameworks before writing backend code.

FastAPI is built for async I/O and long-lived WebSocket connections. Flask is the natural fit for short request/response cycles and synchronous drivers like `pyodbc`. Mixing a sync database driver into an async event loop blocks the entire loop while a query runs — so keeping that work in Flask wasn't a workaround, it was the right design.

```
Game server (FastAPI):        Auth / DB server (Flask):
• persistent WebSocket        • REST endpoints (login, register, scores)
• ~30fps frame stream         • synchronous pyodbc → Azure SQL
• low, predictable latency    • stable, boring request handling
```

> **What I learned:** Choosing a framework is less about loyalty and more about matching strengths to responsibilities. Researching both upfront let me design around their strengths instead of fighting their weaknesses later.

## The Azure SQL cold-start problem

Everything worked locally. After deploying, login started failing intermittently — no clear pattern, no error message I'd written. I spent time convinced it was a Docker networking issue before finding the actual cause.

Azure SQL Serverless auto-pauses after inactivity. The first connection after a pause triggers a resume that can take 15–20 seconds — long enough to exceed a client timeout. The failure looked random because it only happened after idle periods.

```
# cold start sequence
T+0.0s   User submits login form
T+0.1s   Flask opens DB connection → Azure SQL: "Resuming..."
T+5.0s   Client timeout (5s) → retry with wake request
T+15.0s  Still resuming → code -99 returned to frontend
T+15.0s  User sees: "Databass is asleep, float around..."
T+20s    Azure SQL: "Resume complete." — next request succeeds
```

Fix: retry logic with a wake-up request on first failure, longer timeout on the second try, and making the game playable without logging in so a cold DB doesn't block the core experience.

```python
# auth.py — retry + wake on failure (simplified)
for attempt, timeout in enumerate((5, 15)):
    try:
        response = requests.post(f"{BASE_URL}/login",
            json={"username": username, "password": password},
            timeout=timeout)
        ...
    except requests.RequestException:
        if attempt == 0:
            _wake_database()
            continue
        return {"code": -99, "message": DB_ASLEEP_MSG}
```

> **What I learned:** Cloud services have behavior that doesn't exist locally — auto-pause, cold starts, connection limits, regional latency. Building for the cloud means designing for failure, not just the happy path.

## Docker and Azure Container Instances

I planned to containerize at the end. I should have started there.

**Why ACI over AKS or App Service:**  Azure Kubernetes Services (AKS) introduces cluster management that doesn't make sense at this scale. App Service isn't a natural fit for multi-container setups with custom networking. Azure Container Instances (ACI) bills per CPU-second with no idle cost and no infrastructure to manage — right-sized for a low-traffic project on a student budget.

**Container groups:** Locally, Docker Compose lets containers reach each other by service name. In an ACI container group, all containers share a network namespace and communicate over `localhost` instead. One public IP for the group; internal traffic never leaves the host.

```
ACI container group (production)
┌──────────────────────────────────────────────────────┐
│  React + nginx      FastAPI           Flask           │
│  :8080 (public)     :8765 localhost   :5001 localhost │
└──────────────────────────────────────────────────────┘
Local:      service names (docker-compose)
Production: localhost (ACI container group)
```

**Docker build context:** Local builds worked. Building from the project root — as CI does — broke everything.

```bash
COPY failed: file not found in build context: stat requirements.txt
# Same Dockerfile. Different build context.
```

`COPY` resolves paths relative to the build context, not the Dockerfile's location. Fix: explicit contexts per service in Compose.

```yaml
flask-api:
  build:
    context: src
    dockerfile: Dockerfile.web
frontend:
  build:
    context: frontend
    dockerfile: Dockerfile.react
```

A second issue: Alpine Linux doesn't include glibc, which Microsoft's ODBC Driver 18 requires. Switching to `python:3.12-bookworm` fixed it.

```dockerfile
# ❌ ODBC driver unavailable on Alpine
FROM python:3.12-alpine

# ✅ Works
FROM python:3.12-bookworm
RUN apt-get update && apt-get install -y unixodbc-dev curl gnupg \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql18
```

> **What I learned:** Docker build problems and cloud networking problems compound. Treat deployment as part of the design, not an afterthought.

---

## Key takeaways

1. **Protocol choice is an architecture choice.** WebSockets for real-time frames; REST for auth and scores. Polling can't fix structural lag no matter how aggressively you tune the interval.
2. **Match frameworks to responsibilities.** FastAPI for the async game loop; Flask for sync `pyodbc` access to Azure SQL. Researching both upfront made the split feel obvious, not complex.
3. **Cloud services have personalities.** Azure SQL auto-pause is invisible in local development and very visible in production. Design for failure before you hit it.
4. **ACI for small multi-container apps.** No cluster overhead, billed per use — but container groups use `localhost`, not Compose service names. Same containers, different addressing.
5. **Docker build context ≠ Dockerfile location.** Set explicit contexts in Compose. Know your base image's dependencies before optimising for size — Alpine lacks glibc.

---

**Next:** [Part 2 — Optimizing the Flask API](blog2.md)

*[GitHub](https://github.com/dhruv-kurpad/flappy-fish) · [Live demo](http://flappy-fish.westus2.azurecontainer.io)*
