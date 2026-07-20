from runner.sandbox import run_python_submission


def run_case(name, code, **kwargs):
    print(f"\n=== {name} ===")
    result = run_python_submission(code, **kwargs)
    print(result)
    return result


def test_network_isolation():
    code = """
import socket
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(3)
    s.connect(("8.8.8.8", 53))
    print("NETWORK REACHED -- ISOLATION FAILED")
except Exception as e:
    print(f"blocked as expected: {type(e).__name__}: {e}")
"""
    result = run_case("Network isolation", code, timeout_seconds=8)
    if "NETWORK REACHED" in result["stdout"]:
        print("FAIL: container reached the network")
    elif "blocked as expected" in result["stdout"]:
        print("PASS: connection attempt failed as expected")
    else:
        print("UNCLEAR: inspect stdout/stderr above manually")


def test_pids_limit():
    code = """
import subprocess
count = 0
procs = []
try:
    for i in range(200):
        p = subprocess.Popen(["sleep", "5"])
        procs.append(p)
        count += 1
except Exception as e:
    print(f"stopped after spawning {count} processes: {type(e).__name__}: {e}")
else:
    print(f"spawned all {count} without being stopped -- PIDS LIMIT NOT ENFORCED")
"""
    result = run_case("PIDs limit (fork/process spam)", code, timeout_seconds=10, pids_limit=64)
    if "PIDS LIMIT NOT ENFORCED" in result["stdout"]:
        print("FAIL: spawned 200 processes without being capped")
    elif "stopped after spawning" in result["stdout"]:
        print("PASS: process spawning was capped before reaching 200")
    else:
        print("UNCLEAR: inspect stdout/stderr above manually")


def test_timeout_enforced():
    code = """
while True:
    pass
"""
    result = run_case("Timeout enforcement (infinite loop)", code, timeout_seconds=3)
    if result["timed_out"] and result["runtime_seconds"] < 6:
        print(f"PASS: killed at timeout, runtime={result['runtime_seconds']}s")
    else:
        print("FAIL or UNCLEAR: check timed_out flag and runtime above")


def test_memory_limit():
    code = """
try:
    data = bytearray(500 * 1024 * 1024)  # 500MB, over our 256MB cap
    print("ALLOCATED 500MB -- MEMORY LIMIT NOT ENFORCED")
except MemoryError:
    print("blocked with MemoryError as expected")
"""
    result = run_case("Memory limit (over-allocation)", code, timeout_seconds=8, memory_mb=256)
    if "ALLOCATED 500MB" in result["stdout"]:
        print("FAIL: allocated past the memory cap")
    elif result["exit_code"] not in (0, None) or "blocked with MemoryError" in result["stdout"]:
        print(f"PASS (likely): process did not complete normally, exit_code={result['exit_code']}")
    else:
        print("UNCLEAR: inspect stdout/stderr/exit_code above manually")


if __name__ == "__main__":
    test_network_isolation()
    test_pids_limit()
    test_timeout_enforced()
    test_memory_limit()
