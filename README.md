# DevMentor

An online judge, built from scratch, in the shape of LeetCode/Codeforces:
submit code in Python, C++, or Java, get sandboxed execution and a live
verdict per test case. An AI mentor layer (Claude-powered hints and code
review) is planned as a later, fully separate phase — see
[Roadmap](#roadmap).

## Architecture

```
React + Monaco
      │
      ▼
FastAPI Gateway ──── CORS, JWT auth, admin-gated Problems CRUD
      │
      ▼
 PostgreSQL
      │
      ├──────────────┐
      ▼              ▼
Submission API   Docker Socket Proxy ── scoped Docker API access,
      │              │                  no raw socket exposure
      ▼              │
 Redis (Celery       │
  broker + pub/sub)   │
      │              │
      ▼              ▼
judge-worker ──▶ Sandbox containers (Python / C++ / Java)
      │              read-only rootfs, network-disabled,
      │              cap-dropped, resource-limited
      ▼
 Postgres (verdicts + per-test-case results)
      │
      ▼
Redis pub/sub ──▶ FastAPI WebSocket ──▶ React (live verdict push)
```

## Status: Phase 1 core is complete and independently verified. Phase 1 polish and Phase 2+ are not.

This project is being built in phases, with a hard rule: the judge itself
had to be fully working, tested, and secure before any AI work started.

**Done, and proven — not just asserted:**
- Sandboxed execution for Python, C++, and Java, each with real
  adversarial tests (attempted network access, memory over-allocation,
  fork bombs, infinite loops) confirmed to actually fail the way they
  should, not just configured and assumed to work
- Compile-error, runtime-error, wrong-answer, and time-limit-exceeded
  verdicts, correctly distinguished
- An asynchronous judging pipeline: FastAPI accepts a submission and
  returns immediately; Celery + Redis queue the job; a separate
  `judge-worker` container picks it up independently. Verified by
  actually stopping the worker mid-flight and confirming the API kept
  responding rather than blocking
- `judge-worker`'s Docker access goes through a permission-scoped socket
  proxy, not a raw socket mount — it can create/start/stop containers
  and nothing else (no `exec`, no volume management, no image builds)
- Live verdict delivery over WebSocket via Redis pub/sub, instead of
  polling
- JWT auth, admin-gated problem/test-case management with a real
  versioning scheme (a problem's `version` bumps when its test cases
  change, and every submission snapshots the version it was judged
  against)
- A working frontend: auth flow, problem list/detail, a real Monaco
  editor wired to the live submit → judge → verdict loop, and a
  solved-count leaderboard

**Explicitly out of scope for now, pushed to after deployment:**
- **Contest mode** (Phase 1.3 in the original plan) — time-boxed problem
  sets with a live rank during the window. The `Contest` model already
  exists in the schema, but nothing enforces submission windows or shows
  a contest-scoped leaderboard yet. Deliberately sequenced after
  deployment, not before it.

**Explicitly deferred within Phase 1, not forgotten:** **Observability** — no structured logging or Prometheus/Grafana yet
- **Automated test suite** — everything above was verified by hand
  (adversarial scripts, curl sequences, real browser testing), not by a
  CI-run test suite. That's a real gap for a production system, flagged
  here rather than glossed over
- **Deployment** — currently local-only via `docker compose`; no cloud
  deploy yet

**Not started at all:**
- Phase 2 (AI mentor), Phase 3 (learning engine / recommendations),
  Phase 5 (interview mode), plagiarism detection

## Tech stack

- **Backend:** FastAPI, SQLAlchemy (async) + Alembic, PostgreSQL
- **Queue:** Celery + Redis (also used for WebSocket pub/sub)
- **Sandboxing:** Docker, via a permission-scoped socket proxy
  ([Tecnativa/docker-socket-proxy](https://github.com/Tecnativa/docker-socket-proxy))
- **Frontend:** React (Vite), Tailwind v4, Monaco Editor, react-router
- **Auth:** JWT (python-jose), bcrypt via passlib

## Running it locally

```bash
# Backend + judging infra
docker compose up -d --build
docker compose exec api alembic upgrade head

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

API: `http://localhost:8000` · Frontend: `http://localhost:5173`

Promoting a user to admin (no self-service endpoint, by design):
```bash
docker compose exec postgres psql -U devmentor -d devmentor \
  -c "UPDATE users SET is_admin = true WHERE username = 'your_username';"
```

## Known trade-offs, stated plainly

- The Docker socket proxy runs with `security_opt: label:disable` on
  this host, due to an unresolved interaction between SELinux and this
  specific proxy image's haproxy backend — not a general SELinux
  incompatibility (confirmed via `ausearch`, zero denials). The proxy's
  own permission allow-list remains the real access boundary regardless.
- The WebSocket connection registry lives in the API process's memory —
  correct for a single API instance, would need rework (e.g. per-
  connection Redis channels) to support multiple API replicas.
- `test_case_results` is a hand-written SQL table, not yet migrated into
  the Alembic-managed schema alongside everything else — a known,
  intentional piece of schema drift, not an oversight.
- Problem versioning tracks a version *number*, not full historical
  snapshots of past test case content.

## Roadmap

Phase 1 polish (tests, observability, deployment) → Phase 1.3 (contest
mode, scheduled for after deployment) → Phase 2 (AI mentor, as a fully
separate Celery queue/worker so a Claude API outage never blocks
judging) → Phase 3 (learning recommendations) → Phase 5 (interview
mode).
