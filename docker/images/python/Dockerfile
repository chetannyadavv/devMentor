FROM python:3.12-slim

# Non-root user — if sandboxed code ever escapes the container boundary,
# it escapes as this unprivileged user, not root.
RUN useradd --create-home --uid 1000 --shell /usr/sbin/nologin sandbox

WORKDIR /home/sandbox

USER sandbox

# No CMD/ENTRYPOINT with the submission baked in — the runner supplies
# the actual command (e.g. "python solution.py") at container-start time.
