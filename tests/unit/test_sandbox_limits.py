"""
Unit tests for the sandbox's security properties. Run directly against
a Docker daemon -- no full compose stack needed. This is a pytest-ified
version of what we verified by hand: same assertions, now runnable on
their own via `pytest`.
"""
from runner.sandbox import run_python_submission


def test_smoke():
    result = run_python_submission("print('hello from sandbox')")
    assert result["exit_code"] == 0
    assert "hello from sandbox" in result["stdout"]
    assert result["timed_out"] is False


def test_network_is_isolated():
    code = """
import socket
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(3)
    s.connect(("8.8.8.8", 53))
    print("NETWORK REACHED")
except Exception as e:
    print(f"blocked: {type(e).__name__}: {e}")
"""
    result = run_python_submission(code, timeout_seconds=8)
    assert "NETWORK REACHED" not in result["stdout"]
    assert "blocked" in result["stdout"]


def test_pids_limit_is_enforced():
    code = """
import subprocess
count = 0
try:
    for i in range(200):
        subprocess.Popen(["sleep", "5"])
        count += 1
except Exception:
    pass
print(f"spawned {count}")
"""
    result = run_python_submission(code, timeout_seconds=10, pids_limit=64)
    # Should never reach anywhere close to 200 -- the cgroup limit should
    # cap it well below that.
    spawned = int(result["stdout"].strip().split()[-1])
    assert spawned < 100


def test_timeout_is_enforced():
    result = run_python_submission("while True: pass", timeout_seconds=3)
    assert result["timed_out"] is True
    assert result["runtime_seconds"] < 6  # killed near the limit, not left running


def test_memory_limit_is_enforced():
    code = """
data = bytearray(500 * 1024 * 1024)  # 500MB, over the 256MB cap
print("ALLOCATED 500MB")
"""
    result = run_python_submission(code, timeout_seconds=8, memory_mb=256)
    assert "ALLOCATED 500MB" not in result["stdout"]
    assert result["exit_code"] == 137  # SIGKILL, from the OS-level cgroup OOM killer
