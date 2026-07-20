**Part 2 of 3 · Full-Stack Learning Series**

# Optimizing the Flask API

In [Part 1](blog1.md) I walked through building Flappy Fish end to end — terminal game to browser, WebSockets, React, Azure SQL cold starts, and the retry path that keeps login from failing when the database wakes up. This post picks up after that: the app worked, but steady-state requests still felt slow. You do not need the first post to follow this one — the short version is a Flask API talking to Azure SQL over `pyodbc`, where every auth and leaderboard call used to open a brand-new database connection.

**Stack:** Python · Flask · pyodbc · DBUtils · Azure SQL · Gunicorn · cProfile

---

After the game was live, login felt slower than it should. Not broken — the retry logic from Part 1 handled the Azure SQL cold-start — but even when the database was awake, requests took longer than the query itself warranted. I wanted to know where the time was going, not guess.

A [profiler](https://docs.python.org/3/library/profile.html) is a tool that records how much time your program spends in each function while it runs. Instead of staring at a slow endpoint and guessing — "is it the query? the JSON? the network?" — you get a ranked list of what actually burned the milliseconds. For a class project API, that matters: the wrong fix wastes a week, and the right fix is often one boring line in the wrong place.

So I profiled the Flask API before changing anything.

## Where the time was actually going

I wrapped each Flask route in [cProfile](https://docs.python.org/3/library/profile.html) using `@app.before_request` and `@app.after_request`, writing one snapshot per endpoint to `profile/` for the unpooled app and `profile_pool/` for the pooled one. No external APM — just Python's built-in profiler on the code I already had.

A trimmed `/login` snapshot from the unpooled run looked like this:

```text
--- login.prof (total 0.4357s) ---
   ncalls  tottime  cumtime  filename:lineno(function)
        1    0.000    0.436  flask/app.py:879(dispatch_request)
        1    0.000    0.436  flaskapp.py:102(login)
        1    0.000    0.358  flaskapp.py:75(get_db)
        1    0.355    0.357  {built-in method pyodbc.connect}
        1    0.037    0.037  {method 'execute' of 'pyodbc.Cursor' objects}
```

The request took **435.7ms** end to end. **357ms** of that was inside `pyodbc.connect`. The query itself took **37ms**.

I was spending 82% of every request opening a connection that I immediately closed at the end of the handler — so the next request could start from zero again.

> **What I learned:** Profiling made a suspicion concrete. The database wasn't slow. Connection setup was slow. Those are different problems with different fixes — and you can't know which one you have until you measure.

## Opening a connection on every request

The original `get_db()` opened a fresh connection on every request:

```python
def get_db():
    return pyodbc.connect(CONNECTION_STRING, timeout=60)
```

That pattern is fine when you are debugging a single query by hand. In a web API it means every login, register, and leaderboard hit pays a full TLS handshake and ODBC negotiation with Azure SQL before a single `SELECT` runs. After the profiles, that was clearly the tax I was paying.

I looked at a few ways to stop doing that:

| Option | What it is | Why I did / didn't pick it |
|--------|------------|----------------------------|
| Keep per-request `pyodbc.connect` | Open and close every time | Simple, but the profiles showed it was most of the latency |
| [SQLAlchemy](https://docs.sqlalchemy.org/en/20/core/pooling.html) `QueuePool` | Mature ORM/engine pooling | Great if I already used SQLAlchemy. I was on raw `pyodbc` queries, so pulling in an ORM just for a pool felt heavy |
| Roll my own pool | A list of open connections + a lock | Easy to get wrong under concurrency; I did not want to own that code |
| [DBUtils `PooledDB`](https://webwareforpython.github.io/DBUtils/UsersGuide.html#pooleddb) | Small pooling library that wraps a DB-API driver | Drop-in for `pyodbc`, no ORM required, and it matches how Flask routes already looked |

I went with **DBUtils `PooledDB`**. Connections open once and return to the pool when the handler finishes, instead of being torn down:

```python
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

Handlers still call `conn.close()` — with a pool, that means *return to the pool*, not tear down the TCP session. The next request reuses a warm connection and skips most of the handshake cost. The [DBUtils docs](https://webwareforpython.github.io/DBUtils/UsersGuide.html#pooleddb) make that close-vs-return behavior explicit, which is what sold me on it for this codebase.

I kept `mincached=0` deliberately. Eagerly opening connections at import time is a bad fit when Azure SQL may be paused on container start — the first request after idle still pays a connection cost, but after that the pool amortizes it.

| Setting | Value | Why |
|---------|-------|-----|
| `maxcached` | 5 | Keep a handful of idle connections ready |
| `maxconnections` | 10 | Cap total connections under burst traffic |
| `blocking` | True | Wait for a free connection rather than failing immediately |
| `ping` | 1 | Check a connection when it leaves the pool so stale sockets get replaced |
| `failures` | `pyodbc.Error` | Drop bad connections instead of handing them to the next request |

If I were starting again I'd pool from the first deployment, not after noticing latency in manual testing. Per-request connections are fine for a script; they're the wrong default for a web API backed by a remote database.

> **What I learned:** A connection pool isn't an optimization you add later — it's the correct default for any API making repeated calls to a remote database. The per-request pattern hid a cost I was paying on every single request.

## Same endpoints, after the pool

I ran the same endpoint sequence against both local Flask servers while Azure SQL was awake. Each run overwrote the previous snapshot, so these are steady-state numbers — not first-request cold starts.

| Endpoint | Without pool | With pool | Speedup |
|----------|-------------:|----------:|--------:|
| `/getAllPlayers` | 457.9ms | 78.4ms | 5.8× |
| `/login` | 435.7ms | 119.2ms | 3.7× |
| `/register` | 469.7ms | 148.1ms | 3.2× |
| `/updateScore` | 458.2ms | 130.5ms | 3.5× |
| `/delete` | 498.9ms | 117.8ms | 4.2× |

Average request time dropped from **464.1ms to 118.8ms** — a **74% reduction** and roughly **3.9× faster** across all five endpoints.

Faster responses are the obvious win for players. The quieter win is **compute time you no longer bill for**. Azure [Container Apps](https://azure.microsoft.com/en-us/pricing/details/container-apps/) on the Consumption plan charges active usage by the second for allocated vCPU and memory while a replica is handling requests ([billing docs](https://learn.microsoft.com/en-us/azure/container-apps/billing)). Shorter requests mean less active time for the same traffic.

Assumptions for a rough estimate:

- **Traffic:** 1,000 HTTP requests/hour to the Flask API (login, register, score updates, leaderboard), every hour of the month
- **Mix:** treat every request as the measured average above (464.1ms unpooled vs 118.8ms pooled)
- **Replica size:** 0.5 vCPU and 1 GiB — a small Consumption-plan shape for this API
- **Concurrency:** low enough that active replica time ≈ sum of request durations (menu traffic, not a thundering herd)
- **Rates (pay-as-you-go active usage):** $0.000024 per vCPU-second and $0.000003 per GiB-second, from the [public pricing page](https://azure.microsoft.com/en-us/pricing/details/container-apps/)
- **Idle / always-on min replicas:** ignored here — this is only the active-processing slice attributable to request duration
- **Free monthly grant:** 180,000 vCPU-seconds, 360,000 GiB-seconds, and 2 million requests — called out below so the dollar figure is not overstated

At 1,000 requests/hour:

| | Unpooled | Pooled | Saved |
|--|---------:|-------:|------:|
| Active time / hour | 464.1 s | 118.8 s | 345.3 s |
| Active time / month (×730 h) | 338,793 s | 86,724 s | 252,069 s |

Cost of one active replica-second at 0.5 vCPU + 1 GiB:

```text
(0.5 × $0.000024) + (1.0 × $0.000003) = $0.000015 / replica-second
```

Monthly active-usage cost of that request traffic (before free grant):

| | Unpooled | Pooled | Difference |
|--|---------:|-------:|-----------:|
| Billable active usage | ~$5.08 | ~$1.30 | **~$3.78 / month** |

Request metering does not change the story here: 1,000 req/hour is about 730k requests/month, still under the 2 million free requests. The savings are almost entirely from holding the replica active for less time per call.

At this small-scale volume, the free grant can still cover a lot of the absolute bill — so the honest reading is not "I saved $3.78 on my class project invoice," but "the same traffic consumes ~74% less active compute, which is ~$3.78/month of Consumption capacity at list rates, and that gap grows linearly if traffic grows." Latency is what players feel; the cost math is why pooling still matters when the app is no longer a free-tier experiment.

Every unpooled profile told the same story: `pyodbc.connect` consumed 355–386ms before the application ran a single query. In the pooled profiles it disappeared from the hot path entirely. The remaining time was real work — query execution (37–53ms), commits (37–49ms), and returning the connection to the pool (~40ms).

## Pooling doesn't wake a sleeping database

It's worth saying clearly because it's easy to conflate two different problems.

**Connection pooling** optimizes the steady state: database awake, same container process handling repeated traffic.

**Azure SQL auto-pause** is a cold-start problem: the first request after idle may need to wake the server, which can exceed a short client timeout regardless of how good your pool is.

Both layers stayed in place:

1. **Flask + pool** — reuse connections once things are running
2. **`auth.py` retries + wake** — on failure, nudge the database awake with a test login, retry with a longer timeout, return a friendly `-99` if it's still waking

The frontend notice — *"Currently on a free database tier, so the first request may be slow"* — is honest UX for a constraint pooling alone can't remove.

Pooling made the API faster. Retries made it survivable. Neither replaces the other.

> **What I learned:** Two problems can look identical from the outside — slow login — but have completely different causes and fixes. Profiling told me which one I was actually dealing with. Cold-start handling and connection pooling solve different layers of the same symptom.

## Putting the pooled app in production

The pooled app is what ships in the `flask-api` container. `Dockerfile.web` runs Gunicorn with two workers:

```
gunicorn -b 0.0.0.0:5000 -w 2 flaskapp_pool:app
```

Each worker gets its own pool instance — that's normal for WSGI servers, pools are per process. Two workers × up to ten connections sits well within what a small Azure SQL tier expects for this project. Environment variables feed the connection string so credentials aren't baked into the image.

---

## What I'd tell myself next time

1. **Profile before you optimize.** The bottleneck was connection setup, not queries. Could have guessed but seeing for myself is more solid.
2. **Pool right away.** Per-request connections are the wrong default for a web API making repeated calls to a remote database.
3. **Cold starts and steady-state latency are different problems.** Pooling doesn't help a paused database wake up faster. Retries don't help an already-awake database handle traffic efficiently. You need both.
4. **`mincached=0` for serverless databases.** Don't eagerly open connections at import time when the database might be paused — let the first request trigger the wake, then let the pool take over.
5. **Measure the same endpoints twice.** Running profiling on unpooled and pooled versions side by side made the improvement concrete, not anecdotal.

---

**Part 3** — GitHub Actions, ACR, and the `:latest` tag trap that kept the old UI live after a "successful" deploy.

*[GitHub](https://github.com/dhruv-kurpad/flappy-fish) · [Live demo](http://flappy-fish.westus2.azurecontainer.io)*
