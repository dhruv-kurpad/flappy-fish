**Part 3 of 3 · Full-Stack Learning Series**
 
# Shipping With Confidence
 
*The deploy said succeeded. The site showed the old UI. That's when I built a real pipeline.*
 
**Stack:** GitHub Actions · Azure Container Registry · Azure Container Instances · Python unittest · FastAPI · Flask
 
---
 
After Part 2, the app was faster and the architecture was solid. But deploying still meant pushing to `main`, refreshing the live URL, and hoping nothing broke. That's not confidence — it's optimism. So I built a pipeline that gives you an actual reason to trust a deploy.
 
## Making deploy wait for tests
 
A pipeline that always deploys is simple. A pipeline that only deploys when tests pass is useful.
 
```
push to main / manual trigger
        │
        ▼
┌─────────────────────┐
│  Stage 1 — Tests    │  unittest (unit + mocked + live E2E)
└─────────┬───────────┘
          │ all pass
          ▼
┌─────────────────────┐
│  Stage 2 — Deploy   │  build → ACR → ACI (main only)
└─────────────────────┘
```
 
Stage 2 has `needs: test`. If any test fails, deploy never starts. Pull requests run Stage 1 only — feedback without touching production.
 
```yaml
jobs:
  test:
    name: Stage 1 — Tests
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -r src/requirements.txt
      - working-directory: src
        run: python -m unittest test_functional_stub -v
 
  deploy:
    name: Stage 2 — Deploy
    needs: test
    if: github.event_name == 'workflow_dispatch' ||
        (github.event_name == 'push' && github.ref == 'refs/heads/main')
    runs-on: ubuntu-latest
    steps:
      # build three images → push to ACR → az deployment group create
```
 
| Trigger | Stage 1 | Stage 2 |
| --- | --- | --- |
| Pull request | ✅ | ❌ |
| Push to `main` | ✅ | ✅ (if tests pass) |
| Manual `workflow_dispatch` | ✅ | ✅ (if tests pass) |
 
> **What I learned:** You don't need separate workflow files for tests and deploy — one pipeline with a `needs` dependency edge is enough to enforce "green before ship."
 
## What I actually tested — and how
 
The suite started as a checklist — class names and docstrings describing what each test *should* verify, with empty bodies skipped until implemented. That stub became the contract for the whole stack.
 
| Layer | What's tested | How |
| --- | --- | --- |
| Flask API | register, login, scores, delete, validation codes | Flask test client + mocked `pyodbc` |
| Auth bridge | status-code mapping, wake-on-failure, leaderboard shape | Mocked `requests` |
| Game server HTTP | `/auth/register`, `/auth/login`, `/leaderboard`, CORS | FastAPI `TestClient` |
| WebSocket protocol | connect, frames, flap, quit, `game_over` | Scripted `run_game_headless` fakes |
| Game logic | collision, scoring, headless loop, spawner | Direct unit tests on `game_logic.py` |
| Regression guards | Dockerfile CMD, nginx routes, compose `BASE_URL`, deploy image tags | File content assertions |
| Live E2E | register → login → leaderboard, WebSocket play, cold-start UX | HTTP/WS against deployed ACI URL |
 
Most tests are fast and hermetic — no network, no database. The ones that hit production are intentional.
 
## No local Docker needed — test against the real thing
 
I don't run Docker Compose on every machine, and the CI runner doesn't either. Flask isn't exposed publicly in production — only nginx → game-server (`/auth/`, `/leaderboard`, `/ws/`). So the live tests target what players actually use:
 
```
http://flappy-fish.westus2.azurecontainer.io
```
 
That single URL exercises the full path: nginx proxy, FastAPI game server, auth bridge, Flask, Azure SQL. The test registers a throwaway user, logs in, confirms they appear on the leaderboard, opens a WebSocket and receives frames. If the database is cold, the test accepts a graceful JSON response — not a 502 from nginx.
 
```python
DEFAULT_AZURE_APP_URL = "http://flappy-fish.westus2.azurecontainer.io"
 
def _public_api_url() -> str:
    return os.getenv("GAME_SERVER_URL", DEFAULT_AZURE_APP_URL).rstrip("/")
```
 
No env vars required in CI. The deployed URL is the default.
 
> **What I learned:** E2E tests don't have to mean spinning up Compose locally. If production is already reachable, test through the same front door users hit. You're validating the wiring, not just individual containers in isolation.
 
## Why the deploy "worked" but nothing changed
 
Part 1 foreshadowed this. Deploys reported success. The live site still showed the old UI.
 
ACI caches images. If the ARM template says `frontend:latest` and the tag string doesn't change between deploys, Azure has no reason to pull a new layer — even when `:latest` in the registry now points somewhere else.
 
Fix: tag every build with the commit SHA and pass that tag into the deployment template.
 
```yaml
env:
  IMAGE_TAG: ${{ github.sha }}
 
# Build & push — both SHA and :latest
-t ${{ secrets.ACR_LOGIN_SERVER }}/frontend:${{ env.IMAGE_TAG }}
-t ${{ secrets.ACR_LOGIN_SERVER }}/frontend:latest
 
# Deploy — SHA tag forces ACI to pull the new image
--parameters frontendImage=frontend:${{ env.IMAGE_TAG }} \
             flaskApiImage=flask-api:${{ env.IMAGE_TAG }} \
             gameServerImage=game-server:${{ env.IMAGE_TAG }}
```
 
Then restart the container group to force the new image reference to load:
 
```yaml
- name: Restart container group
  run: |
    az container restart \
      --resource-group ${{ secrets.AZURE_RESOURCE_GROUP }} \
      --name flappy-fish
```
 
The regression suite checks for this explicitly — `deploy.yml` must contain `IMAGE_TAG: ${{ github.sha }}` and `frontendImage=frontend:${{ env.IMAGE_TAG }}`. A future edit that reverts to `:latest`-only will fail Stage 1 before it reaches production.
 
> **What I learned:** "Deploy succeeded" and "users see the new build" are different claims. Immutable tags per commit make the second one true — and a regression test makes sure you can't accidentally undo it.
 
## The test that passed locally and failed in CI
 
The first CI run failed on `test_gravity_moves_player_down_without_input`. Locally it passed most of the time.
 
The test inferred the bird's vertical position by scanning the rendered buffer for yellow pixels (`#FFFF00`). The problem: pufferfish obstacles use the same color. Under load on GitHub's runner, the timing was different enough that the test locked onto an obstacle pixel instead of the player and compared the wrong Y values. It looked like a physics bug. It was a test bug.
 
Fix: wrap `render_frame` and record `player.position[1]` directly. Assert the bird falls after the jump apex — not that a buffer sample is below another buffer sample.
 
> **What I learned:** A flaky test in CI is not noise — it's a bug in the test. The failure only showed up on GitHub's runner because timing was different enough to expose the ambiguity. Fix it properly rather than retry until green.
 
---
 
## Key takeaways
 
1. **`needs: test` is the gate.** One workflow, two stages. PRs get test feedback; `main` only ships when everything passes.
2. **Test the public surface.** Live E2E against the deployed ACI URL — no local Compose required, and you're validating real wiring.
3. **Mock what you can; hit prod for what matters.** Unit tests for logic and API contracts; HTTP/WebSocket smoke tests for the full nginx → game-server → auth → SQL path.
4. **Tag images with the commit SHA.** `:latest` alone won't force ACI to pull new layers. Immutable tags per commit will.
5. **Put regression guards in the test suite.** File assertions on Dockerfile CMD, nginx routes, and deploy tags catch config drift before it reaches production.
6. **Flaky tests break the gate.** Diagnose them properly — timing-sensitive buffer scanning is a test design problem, not something to retry past.
---
 
Three posts, one project. Part 1 was about making it work. Part 2 was about making it fast. Part 3 was about making it trustworthy. The game didn't change — but how I think about building and shipping software did.
 
*[Part 1](blog1.md) — terminal to browser · [Part 2](blog2.md) — profiling and connection pooling*
 
*[GitHub](https://github.com/dhruv-kurpad/flappy-fish) · [Live demo](http://flappy-fish.westus2.azurecontainer.io)*