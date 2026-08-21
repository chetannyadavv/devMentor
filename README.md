# DevMentor

An online judge, built from scratch, in the shape of LeetCode/Codeforces:
submit code in Python, C++, or Java, get sandboxed execution and a live
verdict per test case, plus an AI mentor that gives conceptual hints on
failures and brief code review on accepted solutions — architected as a
fully separate service so it can never block or slow down judging.

**Live:** `https://68.210.224.150` (self-signed cert — see [Deployment](#deployment))

## Architecture

```
React + Monaco
      │
      ▼
Nginx ── TLS termination, reverse proxy, serves the built frontend
      │
      ▼
FastAPI Gateway ──── CORS, JWT auth, admin-gated Problems/Contest CRUD
      │
      ▼
 PostgreSQL
      │
      ├──────────────────────────────┐
      ▼                              ▼
Submission API                Docker Socket Proxy ── scoped Docker API
      │                              │                access, no raw
      ▼                              │                socket exposure
 Redis (Celery broker + pub/sub)     │
      │              │               │
      ▼              ▼               │
judge-worker    ai-worker            │
      │         (separate queue,     │
      │          separate container, │
      │          no Docker access    │
      │          at all)             │
      ▼              │               │
Sandbox containers ◀──────────────────┘
(Python/C++/Java)    │
read-only rootfs,    ▼
network-disabled,   Gemini API (hints on failure,
cap-dropped,        code review on ACCEPTED)
resource-limited          │
      │                   ▼
      ▼            writes ai_feedback_text back
 Postgres (verdicts + per-test-case results
           + AI feedback, polled by frontend)
      │
      ▼
Redis pub/sub ──▶ FastAPI WebSocket ──▶ React (live verdict push)

Both api and judge-worker also expose /metrics (Prometheus), scraped
into Grafana. All three worker processes emit structured JSON logs,
correlatable by submission_id.
```

## Status: Phase 1 core, observability, automated tests, contest mode, AI mentor, and deployment are all complete and independently verified.

This project was built in phases, with a hard rule that held throughout:
the judge itself had to be fully working, tested, secure, and deployed
before any AI work started — so the AI layer never became a way of
skipping the less exciting finishing work.

**Done, and proven — not just asserted:**
- Sandboxed execution for Python, C++, and Java, each with real
  adversarial tests (attempted network access, memory over-allocation,
  fork bombs, infinite loops) confirmed to actually fail the way they
  should
- Compile-error, runtime-error, wrong-answer, and time-limit-exceeded
  verdicts, correctly distinguished
- An asynchronous judging pipeline: FastAPI accepts a submission and
  returns immediately; Celery + Redis queue the job; a separate
  `judge-worker` container picks it up independently. Verified by
  actually stopping the worker mid-flight and confirming the API kept
  responding rather than blocking
- `judge-worker`'s Docker access goes through a permission-scoped socket
  proxy, not a raw socket mount
- Live verdict delivery over WebSocket via Redis pub/sub, instead of
  polling
- JWT auth, admin-gated problem/test-case/contest management, with a
  real problem versioning scheme (version bumps when test cases change,
  submissions snapshot which version they were judged against)
- **Contest mode**: time-boxed problem sets, admin-gated creation,
  problems hidden from non-admins until the contest starts, a
  contest-scoped leaderboard computed from `submitted_at` falling
  inside the window (not a stored flag, so extending a deadline later
  retroactively includes earlier submissions correctly)
- A working frontend: auth, problem list/detail, a real Monaco editor
  wired to the live submit → judge → verdict loop, a leaderboard, a
  contest UI, and an admin panel for creating problems/test
  cases/contests without touching the API by hand
- **AI mentor**: a completely separate `ai-worker` container consuming
  its own Celery queue (`ai_queue`) — `judge-worker` only ever knows a
  task *name* to enqueue, never imports an AI SDK, never waits on a
  response. If the AI provider is down or rate-limited, judging is
  entirely unaffected; the frontend just shows feedback as
  "unavailable." The system prompt explicitly refuses to hand over
  corrected/solution code, even when a submission's comments ask for it
  directly — verified against a real adversarial prompt, not just
  stated as an intention
- **Observability**: structured JSON logs correlatable by
  `submission_id` across all three worker processes, real Prometheus
  metrics (request latency, judge duration by language, submission
  counts by verdict, active sandbox count, live queue length),
  visualized in Grafana
- **Automated tests**: unit tests for sandbox security limits and judge
  verdict logic (Python/C++/Java), plus integration tests that hit the
  real running API end-to-end
- **Deployed**: a real Azure VM (Ubuntu, Docker installed from scratch),
  reachable over the public internet, TLS-terminated, survived multiple
  multi-day gaps and reboots with zero manual recovery needed beyond
  `docker compose up -d`

**Deliberately cut, not forgotten — and why:**
- **Phase 3 (learning engine / topic recommendations)** and **Phase 5
  (interview mode)** were both scoped out. Phase 3 specifically would
  have required a real, multi-topic, hand-verified problem set just to
  make per-topic accuracy tracking demonstrable — genuine content work
  with no new infrastructure lesson behind it. Better use of the
  remaining time was doing the AI mentor (Phase 2) properly than three
  features shallowly.
- **Plagiarism detection** (AST-diff/token similarity) — noted in the
  original plan as a good standalone topic, never built.

## The Caddy → Nginx story

Worth keeping in the record rather than smoothing over: the reverse
proxy was originally built on Caddy for its automatic-HTTPS convenience.
On the deployed VM, Caddy generated valid, correctly-matched certificate
and key files every time, but consistently failed the TLS handshake
itself with `internal error` — reproduced identically regardless of
certificate source (automatic vs. manually supplied), TLS version
(1.2 and 1.3 both failed the same way), HTTP/3 on or off, and even from
a fully wiped, from-scratch certificate volume. Every variable that
could be isolated was isolated methodically, one at a time, with real
evidence at each step (`openssl s_client`, packet-level TLS alerts,
direct file/permission checks) before concluding it was something
specific to that Caddy build in this environment, not our configuration.
Nginx, using a completely different TLS stack, handled the identical
certificate cleanly on the first real test — conclusive, not just
convenient. The swap took under an hour once the decision was made.

## Tech stack

- **Backend:** FastAPI, SQLAlchemy (async) + Alembic, PostgreSQL
- **Queue:** Celery + Redis (also used for WebSocket pub/sub)
- **Sandboxing:** Docker, via a permission-scoped socket proxy
  ([Tecnativa/docker-socket-proxy](https://github.com/Tecnativa/docker-socket-proxy))
- **AI:** Google Gemini API (`gemini-3.1-flash-lite-preview`) — chosen
  specifically for having a genuine no-credit-card free tier
- **Reverse proxy / TLS:** Nginx
- **Observability:** Prometheus, Grafana, structured JSON logging
- **Testing:** pytest (unit + integration)
- **Frontend:** React (Vite), Tailwind v4, Monaco Editor, react-router
- **Auth:** JWT (python-jose), bcrypt via passlib
- **Deployment:** Azure VM (Ubuntu 24.04), Docker Compose, self-signed
  TLS cert (no purchased domain yet)

## Running it locally

```bash
cp .env.example .env
# fill in POSTGRES_PASSWORD, JWT_SECRET_KEY, GRAFANA_ADMIN_PASSWORD
# (openssl rand -hex 32 works for all three), and GEMINI_API_KEY
# (free, no card, from aistudio.google.com/apikey)

mkdir -p certs
openssl req -x509 -newkey ec -pkeyopt ec_paramgen_curve:prime256v1 \
  -keyout certs/key.pem -out certs/cert.pem -days 365 -nodes -subj "/CN=localhost"

docker compose up -d --build
docker compose exec api alembic upgrade head

# Seed 5 hand-verified problems (Two Sum, FizzBuzz, Palindrome Check,
# Binary Search, Maximum Subarray)
python3 seed_problems.py <your_username> <your_password>
```

Frontend and API are both served through Nginx at `https://localhost`
(self-signed cert — expect a browser warning, same as the live
deployment). Prometheus: `http://localhost:9090`. Grafana:
`http://localhost:3000`.

Promoting a user to admin (no self-service endpoint, by design):
```bash
docker compose exec postgres psql -U devmentor -d devmentor \
  -c "UPDATE users SET is_admin = true WHERE username = 'your_username';"
```

## Deployment

Deployed on a real Azure VM (`Standard_B2ls_v2`, Ubuntu 24.04), provisioned
under the GitHub Student Developer Pack's Azure credit. Notes worth
knowing if reproducing this:
- Azure for Students restricts deployable regions per-subscription —
  check `Policy > Assignments > Allowed resource deployment regions`
  before picking a size/region combination, rather than guessing
- VM-level firewall (Network Security Group) needs explicit inbound
  rules for 80/443 — SSH-only by default
- No purchased domain currently — `DOMAIN` in `.env` is the VM's raw
  public IP, which Nginx serves over a self-signed cert (browsers show
  "Not Secure," expected and understood, not a bug)

```bash
ssh -i your-key.pem user@your-vm-ip
git clone https://github.com/chetannyadavv/devMentor.git && cd devMentor
# create .env and certs/ as above, using the VM's real IP for CN
docker build -t devmentor-python-sandbox docker/images/python/
docker build -t devmentor-cpp-sandbox docker/images/cpp/
docker build -t devmentor-java-sandbox docker/images/java/
docker compose up -d --build
docker compose exec api alembic upgrade head
python3 seed_problems.py <username> <password>
```

## Running the tests

```bash
pip install -r requirements.txt

pytest tests/unit -v          # needs a Docker daemon, not the full stack
pytest tests/integration -v -m integration   # needs the full compose stack
pytest -v                     # everything
```

## Known trade-offs, stated plainly

- The Docker socket proxy runs with `security_opt: label:disable` on
  the deployment host, due to an unresolved interaction between SELinux
  and this specific proxy image's haproxy backend — not a general
  SELinux incompatibility (confirmed via `ausearch`, zero denials). The
  proxy's own permission allow-list remains the real access boundary.
- The WebSocket connection registry lives in the API process's memory —
  correct for a single API instance, would need rework for multiple
  API replicas.
- `test_case_results` is a hand-written SQL table, not yet migrated
  into the Alembic-managed schema — known, intentional schema drift.
- Problem versioning tracks a version *number*, not full historical
  snapshots of past test case content.
- The `active_sandboxes` metric approximates "judging operations in
  flight," not an exact per-container count.
- No CI — tests exist and pass locally but don't run automatically on
  push. Deliberately deferred past deployment; a reasonable next step.
- No purchased domain — self-signed cert, raw IP.

## Roadmap

CI → a real domain (upgrades the deployment from self-signed to a
trusted Let's Encrypt cert automatically) → plagiarism detection
(AST-diff/token similarity — no AI needed, a strong standalone topic on
its own). Phase 3 and Phase 5 are deliberately not planned further, per
the reasoning above.
