import os
import shutil
import tempfile
import time
import uuid

import docker

PYTHON_IMAGE = "devmentor-python-sandbox"
CPP_IMAGE = "devmentor-cpp-sandbox"
JAVA_IMAGE = "devmentor-java-sandbox"

COMPILE_ERROR_MARKER = "__DEVMENTOR_COMPILE_ERROR__"

# Set only inside judge-worker (Docker-outside-of-Docker / sibling
# containers). judge-worker is itself a container, so a plain
# tempfile.mkdtemp() creates a directory only IT can see -- the host
# daemon has no idea it exists, and silently mounts an empty directory
# into the sandbox container instead. The fix: judge-worker writes into
# a directory that's ALSO bind-mounted in from the real host (same as
# ./app is), and we track two paths -- the path judge-worker itself uses
# to read/write, and the corresponding real host path we tell the Docker
# daemon to mount into the sibling sandbox container. When unset
# (running directly against a host daemon, as in all our earlier
# standalone testing), this falls back to plain tempfile.mkdtemp() --
# both paths are identical in that case.
SUBMISSIONS_LOCAL_DIR = os.environ.get("SUBMISSIONS_LOCAL_DIR")
SUBMISSIONS_HOST_DIR = os.environ.get("SUBMISSIONS_HOST_DIR")


def _make_submission_dirs():
    if SUBMISSIONS_LOCAL_DIR and SUBMISSIONS_HOST_DIR:
        submission_id = uuid.uuid4().hex
        local_dir = os.path.join(SUBMISSIONS_LOCAL_DIR, submission_id)
        host_dir = os.path.join(SUBMISSIONS_HOST_DIR, submission_id)
        os.makedirs(local_dir, mode=0o755)
        return local_dir, host_dir
    else:
        local_dir = tempfile.mkdtemp(prefix="devmentor-submission-")
        return local_dir, local_dir  # identical -- no DooD indirection needed


def _run_in_container(
    image: str,
    files: dict,
    shell_command: str,
    timeout_seconds: int = 5,
    memory_mb: int = 256,
    pids_limit: int = 64,
) -> dict:
    """
    Shared core: writes `files` (name -> content) into an ephemeral,
    read-only bind-mounted temp dir, runs `shell_command` inside a locked-
    down container, and returns raw exit_code/stdout/stderr/runtime/timed_out.
    No verdict logic here -- that's the judge layer's job.
    """
    client = docker.from_env()

    local_dir, host_dir = _make_submission_dirs()
    try:
        for filename, content in files.items():
            path = os.path.join(local_dir, filename)
            with open(path, "w") as f:
                f.write(content)
            os.chmod(path, 0o644)
        os.chmod(local_dir, 0o755)

        container = client.containers.create(
            image=image,
            command=["sh", "-c", shell_command],
            network_disabled=True,
            mem_limit=f"{memory_mb}m",
            memswap_limit=f"{memory_mb}m",
            pids_limit=pids_limit,
            read_only=True,
            # Docker's default tmpfs mount includes noexec -- fine for
            # Python (interpreted) but blocks compiled C++/Java output
            # from running out of /tmp with exit 126 ("Permission
            # denied"). Confirmed via /proc/mounts. Explicitly opting into
            # exec here, only because compiled-language judging needs it.
            tmpfs={"/tmp": "rw,exec,noatime"},
            cap_drop=["ALL"],
            security_opt=["no-new-privileges"],
            working_dir="/sandbox",
            # Uses the REAL HOST path, not judge-worker's own view of it
            # -- see _make_submission_dirs() above.
            volumes={host_dir: {"bind": "/sandbox", "mode": "ro,Z"}},
            detach=True,
        )

        try:
            start = time.monotonic()
            container.start()

            timed_out = False
            exit_code = None
            try:
                result = container.wait(timeout=timeout_seconds)
                exit_code = result.get("StatusCode")
            except Exception:
                timed_out = True
                container.kill()

            runtime = time.monotonic() - start

            stdout = container.logs(stdout=True, stderr=False).decode("utf-8", errors="replace")
            stderr = container.logs(stdout=False, stderr=True).decode("utf-8", errors="replace")

            return {
                "exit_code": exit_code,
                "stdout": stdout,
                "stderr": stderr,
                "runtime_seconds": round(runtime, 3),
                "timed_out": timed_out,
            }
        finally:
            container.remove(force=True)
    finally:
        shutil.rmtree(local_dir, ignore_errors=True)


def run_python_submission(source_code: str, stdin_data: str = "", **kwargs) -> dict:
    files = {"solution.py": source_code, "input.txt": stdin_data}
    shell_command = "python /sandbox/solution.py < /sandbox/input.txt"
    result = _run_in_container(PYTHON_IMAGE, files, shell_command, **kwargs)
    result["compile_error"] = False
    return result


def run_cpp_submission(source_code: str, stdin_data: str = "", **kwargs) -> dict:
    files = {"solution.cpp": source_code, "input.txt": stdin_data}
    shell_command = (
        "g++ -O2 -o /tmp/a.out /sandbox/solution.cpp 2> /tmp/cerr.txt; "
        "if [ $? -ne 0 ]; then "
        f"echo '{COMPILE_ERROR_MARKER}' >&2; cat /tmp/cerr.txt >&2; exit 1; "
        "else "
        "/tmp/a.out < /sandbox/input.txt; "
        "fi"
    )
    result = _run_in_container(CPP_IMAGE, files, shell_command, **kwargs)

    if COMPILE_ERROR_MARKER in result["stderr"]:
        result["compile_error"] = True
        result["stderr"] = result["stderr"].replace(COMPILE_ERROR_MARKER, "").strip()
    else:
        result["compile_error"] = False

    return result


def run_java_submission(source_code: str, stdin_data: str = "", **kwargs) -> dict:
    # Java requires the filename to match the public class name exactly.
    # We standardize on requiring submissions to define `public class
    # Solution`.
    files = {"Solution.java": source_code, "input.txt": stdin_data}
    shell_command = (
        "javac /sandbox/Solution.java -d /tmp 2> /tmp/cerr.txt; "
        "if [ $? -ne 0 ]; then "
        f"echo '{COMPILE_ERROR_MARKER}' >&2; cat /tmp/cerr.txt >&2; exit 1; "
        "else "
        "java -cp /tmp Solution < /sandbox/input.txt; "
        "fi"
    )
    result = _run_in_container(JAVA_IMAGE, files, shell_command, **kwargs)

    if COMPILE_ERROR_MARKER in result["stderr"]:
        result["compile_error"] = True
        result["stderr"] = result["stderr"].replace(COMPILE_ERROR_MARKER, "").strip()
    else:
        result["compile_error"] = False

    return result
