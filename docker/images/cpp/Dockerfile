FROM gcc:13-bookworm

# Non-root user -- same reasoning as the Python image: if sandboxed code
# ever escapes the container boundary, it escapes as this unprivileged
# user, not root.
RUN useradd --create-home --uid 1000 --shell /usr/sbin/nologin sandbox

WORKDIR /home/sandbox

USER sandbox

# No CMD/ENTRYPOINT baked in -- the runner supplies the compile+run
# command at container-start time.
