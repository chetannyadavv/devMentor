"""
Unit tests for judge verdict logic (Java). Includes the memory test
specifically, since Java's cgroup-aware JVM heap sizing behaves
differently from Python/C++'s raw SIGKILL -- a real, worth-keeping
distinction we found by hand earlier.
"""
from runner.judge import judge_single_case


def test_accepted():
    code = """
import java.util.Scanner;
public class Solution {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int a = sc.nextInt();
        int b = sc.nextInt();
        System.out.println(a + b);
    }
}
"""
    result = judge_single_case(code, stdin_data="3 4", expected_output="7", language="java")
    assert result["verdict"] == "ACCEPTED"


def test_compile_error():
    code = """
public class Solution {
    public static void main(String[] args) {
        this is not valid java at all
    }
}
"""
    result = judge_single_case(code, stdin_data="", expected_output="anything", language="java")
    assert result["verdict"] == "COMPILE_ERROR"


def test_runtime_error():
    code = """
public class Solution {
    public static void main(String[] args) {
        int[] arr = new int[1];
        System.out.println(arr[5]);
    }
}
"""
    result = judge_single_case(code, stdin_data="", expected_output="anything", language="java")
    assert result["verdict"] == "RUNTIME_ERROR"


def test_memory_limit_caught_by_jvm_heap():
    # Java's memory ceiling shows up differently than Python/C++: the
    # JVM is cgroup-aware and sizes its own heap accordingly, so this
    # gets caught gracefully (OutOfMemoryError, clean exit) rather than
    # an OS-level SIGKILL.
    code = """
public class Solution {
    public static void main(String[] args) {
        byte[] data = new byte[800 * 1024 * 1024];
        System.out.println("ALLOCATED 800MB");
    }
}
"""
    from runner.sandbox import run_java_submission

    result = run_java_submission(code, stdin_data="", timeout_seconds=8, memory_mb=256)
    assert "ALLOCATED 800MB" not in result["stdout"]
    assert "OutOfMemoryError" in result["stderr"]
