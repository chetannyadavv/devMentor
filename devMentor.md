# DevMentor — Build Plan

Guiding rule from the review, and the one we'll actually follow:
**Finish Phase 1 completely — tests, deploy, docs, monitoring, polished UI —
before touching AI.** A rock-solid judge is already resume-worthy. AI
enhances it; it doesn't rescue an unfinished foundation.

Final target architecture:

```
React + Monaco
      │
      ▼
FastAPI Gateway
      │
      ▼
 PostgreSQL
      │
      ├──────────────┐
      ▼              ▼
 Judge Queue     AI Queue        ← separate queues (review point 2/3/10)
      │              │
      ▼              ▼
Judge Workers    AI Workers      ← independent, AI worker can die without
      │              │             blocking judging
      ▼              ▼
Docker Runner    Claude API
      │
      ▼
WebSocket Events                 ← review point 9
      │
      ▼
   React UI
```

---

## Phase 1 — Online Judge (core, AI-free)

Ship this completely before Phase 2. Nothing below is optional.

### 1.1 Foundations
- [ ] Repo scaffold, docker-compose (postgres, redis, api, judge-worker)
- [ ] DB schema: users, problems, test ccases, submissions, topics, contests
- [ ] Problem **versioning**: `Problem.version`, `Submission.problem_version`
      snapshot (review point 4)
- [ ] Auth: register/login, JWT
- [ ] Problems CRUD (admin-gated) + test case management

### 1.2 Judging pipeline
- [ ] Submission API → enqueues job, returns immediately (no blocking)
- [ ] Sandboxed executor: disposable Docker container per run, no network,
      CPU/mem/pids caps, read-only fs, non-root user
- [ ] Judge task: run all test cases, produce verdict
- [ ] **Execution artifacts** (review point 6): persist `TestCaseResult` per
      test case — stdout, stderr, exit code, runtime, memory — not just a
      final verdict. Model is done, wiring into the judge task is not.
- [ ] **WebSockets** (review point 9): judge worker publishes a "submission
      updated" event → FastAPI pushes it over a websocket → frontend updates
      live instead of polling.
- [ ] **Submission Replay UI**: step through Test 1 ✓ → Test 2 ✓ → Test 3 ✗
      using the stored per-test artifacts.

### 1.3 Competitive features
- [ ] Leaderboard (solved-count based)
- [ ] Contest mode: time-boxed problem sets, live rank during the window

### 1.4 Frontend
- [ ] React + Monaco editor
- [ ] Problem list / detail / statement rendering
- [ ] Submit flow wired to websocket-driven live verdict
- [ ] Leaderboard + contest views

### 1.5 Production-grade concerns (what separates this from a toy project)
- [ ] **Observability** (review point 5): structured logging, Prometheus
      metrics (judge time, queue length, running containers, success rate),
      Grafana dashboard
- [ ] Tests: unit tests for judge logic/sandbox limits, integration tests
      for the submit → verdict flow
- [ ] Deployment: docker-compose for prod, or a simple cloud deploy
      (Fly.io / Railway / a single VM) with a real domain
- [ ] README with architecture diagram, setup instructions, demo GIF

**Exit criteria for Phase 1:** a stranger can register, browse problems,
submit code in 3 languages, see live pass/fail per test case, appear on
a leaderboard, and you can point to a Grafana dashboard and explain what
happens when 50 submissions land at once.

---

## Phase 2 — AI Mentor (starts only after Phase 1 exit criteria met)

- [ ] **Separate AI queue/worker** (review point 2/3/10) — judge worker
      never calls Claude directly or waits on it. On judge completion it
      emits an event; a dedicated AI worker consumes it independently.
      If Claude is down, the judge still works and the AI panel just shows
      "pending."
  - Code for this already sketched (`app/ai/mentor.py`); needs to move out
    of the judge task into its own Celery queue (`ai_queue`) with its own
    worker process in docker-compose.
- [ ] Hint generation on failure — conceptual only, never a full solution
      (review point 7, already enforced via system prompt)
- [ ] Code review on Accepted (complexity, style, edge cases) — same
      isolation rules apply

## Phase 3 — Learning Engine
- [ ] Topic-tagging on problems (schema already supports this)
- [ ] Per-user topic accuracy aggregation
- [ ] AI-generated "next 5 problems" recommendation, fed by that aggregation

## Phase 4 — AI Code Review
- Folded into Phase 2's AI worker — same infra, different prompt

## Phase 5 — Interview Mode
- [ ] Multi-turn Claude conversation that questions the user about their
      own accepted submission (why DFS, complexity, scaling)

## Later / stretch
- [ ] **Plagiarism detection** (review point 8): AST-diff or token-based
      similarity (Winnowing/MOSS-style) across submissions for the same
      problem — no AI needed, and it's a strong standalone interview topic

---

## What changes from what I already wrote

The judge task (`app/workers/tasks.py`) currently calls the AI mentor
inline — that was me reacting to your review mid-build instead of
replanning first, exactly what you just called out. Once we resume
building, that call gets removed from the judge task and the AI queue
becomes its own thing, done in Phase 2, not now.
