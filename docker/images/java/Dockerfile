FROM eclipse-temurin:21-jdk-jammy

# Non-root user -- same reasoning as Python/C++ images.
RUN useradd --create-home --uid 1000 --shell /usr/sbin/nologin sandbox

WORKDIR /home/sandbox

USER sandbox

# No CMD/ENTRYPOINT baked in -- the runner supplies the compile+run
# command at container-start time.
