from runner.sandbox import run_java_submission

code = """
public class Solution {
    public static void main(String[] args) {
        byte[] data = new byte[800 * 1024 * 1024]; // 800MB, well over our 256MB cap
        System.out.println("ALLOCATED 800MB -- MEMORY LIMIT NOT ENFORCED");
    }
}
"""

result = run_java_submission(code, stdin_data="", timeout_seconds=8, memory_mb=256)
print(result)

if "ALLOCATED 800MB" in result["stdout"]:
    print("FAIL: allocated past the memory cap")
elif result["exit_code"] == 137:
    print("PASS: killed by OS-level cgroup OOM (SIGKILL) -- same mechanism as Python/C++")
elif "OutOfMemoryError" in result["stderr"]:
    print("PASS: caught gracefully by JVM's own cgroup-aware heap sizing (OutOfMemoryError)")
elif result["exit_code"] not in (0, None):
    print(f"PASS (likely): did not complete normally, exit_code={result['exit_code']} -- inspect stderr above")
else:
    print("UNCLEAR: inspect stdout/stderr/exit_code above manually")
