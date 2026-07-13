# Optimizing the Flask API: Profiling, Connection Pooling, and Azure SQL

**Stack:** Python · Flask · pyodbc · DBUtils · Azure SQL · Gunicorn · cProfile  
**Theme:** The first blog ended with a working system and a fragile database layer. This one is about measuring that fragility, fixing the steady-state path, and learning where pooling helps — and where it does not.

In [the first post](blog1-2.md), I described porting a terminal Python game to the browser: WebSockets for real-time frames, Flask for auth and leaderboards, Azure SQL on a free tier. That architecture worked, but the database path had a problem I only half-solved at the time. Retries and longer timeouts kept the app from failing outright when Azure SQL woke from auto-pause, yet every successful request still paid the full cost of opening a new ODBC connection.

Once the game was live, I wanted to know *where* the time was going — not guess. So I profiled the Flask API, replaced per-request connections with a pool, and shipped the pooled version as the production container. The result was a backend that felt much snappier under normal load, without undoing the cold-start handling I still needed on the client side.

---

## Starting with measurement, not assumptions

Before changing anything, I wrapped each Flask route in **cProfile** using `@app.before_request` and `@app.after_request` hooks. Every endpoint wrote a snapshot to a `profiles/` directory — one file per route (`login.prof`, `get_all_players.prof`, `register.prof`, and so on). That made it easy to compare endpoints side by side and export timings into other tools later.

The pattern was simple: enable the profiler when a request arrives, disable it before the response leaves, dump stats keyed by endpoint name. No external APM, no guesswork — just Python’s built-in profiler on the code I already had.

When I sorted by cumulative time on `/login`, the story was obvious. A single request spent on the order of **700ms** end to end. The SQL query itself was fast. **`pyodbc.connect` was not** — opening a fresh connection on every call accounted for a large fraction of the wall clock. Closing the connection at the end of the handler meant the next request started from zero again.

That matched what I already suspected from the cold-start work in the first blog, but profiling made it concrete: even when the database was awake, I was treating connection setup as free. It is not free on Azure SQL, especially over TLS with ODBC Driver 18.

---

## Per-request connections vs. a pool

The original `get_db()` looked like this in spirit:

```python
def get_db():
    return pyodbc.connect(CONNECTION_STRING, timeout=60)
```

Each route opened a connection, ran one or two statements, and closed it in a `finally` block. Correct, easy to reason about, and expensive at scale.

The optimized version lives in `flaskapp_pool.py` and uses **DBUtils `PooledDB`**:

```python
def _create_connection():
    return pyodbc.connect(_CONNECTION_STRING, timeout=60)

_create_connection.dbapi = pyodbc

_pool = PooledDB(
    creator=_create_connection,
    failures=(pyodbc.Error,),
    mincached=0,        # don't connect at import — Azure SQL may be paused
    maxcached=5,
    maxconnections=10,
    blocking=True,
    ping=1,             # verify connection when taken from pool
)

def get_db():
    return _pool.connection()
```

Handlers still call `conn.close()` when they finish. With a pool, **close means return to the pool**, not tear down the TCP session. The next `/login` or `/getAllPlayers` can reuse a warm connection and skip most of the handshake cost.

I kept **`mincached=0`** on purpose. Eagerly opening connections at import time is a bad fit for serverless Azure SQL that may be paused when the container starts. The first request after idle may still pay a connection cost; after that, the pool amortizes it.

Other settings were pragmatic defaults for a small game API:

| Setting | Value | Why |
|---------|-------|-----|
| `maxcached` | 5 | Keep a handful of idle connections ready |
| `maxconnections` | 10 | Cap total connections under burst traffic |
| `blocking` | True | Wait for a free connection instead of failing immediately |
| `ping` | 1 | Check a connection when it leaves the pool so stale sockets get replaced |
| `failures` | `pyodbc.Error` | Drop bad connections instead of handing them to the next request |

Every route uses the same shape: acquire from the pool, work, commit when needed, **always** close in `finally`. That discipline matters — leaking pooled connections exhausts the pool quickly.

---

## What changed in the numbers

Profiling after the switch told a different story on hot paths.

For **`/getAllPlayers`** with pooling enabled, cumulative time dropped to roughly **70ms** on the same machine, and the top of the profile was the query and result mapping — not `pyodbc.connect`. Connection acquisition disappeared from the headline because the pool had already done that work.

For **`/login`** on the *unpooled* path, connect time still dominated. Pooling does not magically fix a cold database, but it removes repeated connect overhead once the service and database are both warm. Leaderboard loads and back-to-back auth calls — common in a game menu — benefit immediately.

I left cProfile hooks commented out in the pooled file used for deployment so production stays lean. The `profiles/` snapshots remain useful artifacts from the optimization pass itself.

---

## Pooling does not replace cold-start handling

This is the part worth saying clearly because it is easy to conflate two different problems.

**Connection pooling** optimizes the steady state: many requests, database already awake, same container process handling traffic over time.

**Azure SQL auto-pause** is a cold-start problem: the first request after idle may need to wake the server, which can exceed a short client timeout no matter how good your pool is.

So I kept both layers:

1. **Flask + pool** — reuse connections inside the API once things are running  
2. **`auth.py` retries + wake** — on failure, POST a login as a known test user to nudge the database awake, retry with a longer timeout, and return a friendly `-99` message if the DB is still sleeping  

The frontend notice — *“Currently on a free database tier, so connection may be slow for the first request”* — is honest UX for a constraint pooling alone cannot remove.

Pooling made the API faster; retries made it survivable. Neither replaces the other.

---

## Shipping it: Gunicorn and Docker

The pooled app is what ships in the **`flask-api`** container. `Dockerfile.web` copies `flaskapp_pool.py` and runs Gunicorn with two workers:

```text
gunicorn -b 0.0.0.0:5000 -w 2 flaskapp_pool:app
```

Each worker process gets its own pool instance. That is normal for WSGI servers: pools are per process, not global across workers. Two workers × up to ten connections is still well within what a small Azure SQL tier expects for this project, and it matches the lightweight traffic pattern of a class game.

Environment variables (`SERVER`, `DATABASE`, `UID`, `PWD`) feed the connection string so credentials are not baked into the image. The pool configuration stays in code because it expresses policy — how aggressive to be about caching and validation — not secrets.

---

## What I would do differently next time

If I were starting again, I would **profile earlier** and **pool from the first deployment**, not after noticing latency in manual testing. The per-request pattern is fine for a script; it is the wrong default for a web API backed by a remote database.

I would also separate three concerns explicitly in documentation:

- **Latency** → pooling, query shape, indexes  
- **Availability on wake** → retries, timeouts, graceful degradation in the UI  
- **Observability** → lightweight profiling or structured timing logs per endpoint  

For Flappy Fish, the optimization story had a satisfying arc: measure, identify connect overhead, introduce `PooledDB` with Azure-aware settings, keep the cold-start path I already built, and deploy the pooled module as the real service. The game engine did not change. The WebSocket layer did not change. The Flask API got faster in the common case — which is exactly the kind of optimization worth writing down.
