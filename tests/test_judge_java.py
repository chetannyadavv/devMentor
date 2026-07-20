from runner.judge import judge_single_case, judge_submission


def test_java_accepted():
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
    print("ACCEPTED case:", result["verdict"], result["stdout"])
    assert result["verdict"] == "ACCEPTED"


def test_java_compile_error():
    code = """
public class Solution {
    public static void main(String[] args) {
        this is not valid java at all
    }
}
"""
    result = judge_single_case(code, stdin_data="", expected_output="anything", language="java")
    print("COMPILE_ERROR case:", result["verdict"], result["stderr"][:100])
    assert result["verdict"] == "COMPILE_ERROR"


def test_java_runtime_error():
    code = """
public class Solution {
    public static void main(String[] args) {
        int[] arr = new int[1];
        System.out.println(arr[5]);  // ArrayIndexOutOfBoundsException
    }
}
"""
    result = judge_single_case(code, stdin_data="", expected_output="anything", language="java")
    print("RUNTIME_ERROR case:", result["verdict"], "exit_code:", result["exit_code"])
    assert result["verdict"] == "RUNTIME_ERROR"


def test_java_tle():
    code = """
public class Solution {
    public static void main(String[] args) {
        while (true) {}
    }
}
"""
    result = judge_single_case(
        code, stdin_data="", expected_output="anything", language="java", timeout_seconds=3
    )
    print("TLE case:", result["verdict"], result["runtime_seconds"])
    assert result["verdict"] == "TIME_LIMIT_EXCEEDED"


if __name__ == "__main__":
    test_java_accepted()
    test_java_compile_error()
    test_java_runtime_error()
    test_java_tle()
    print("\nALL JAVA JUDGE TESTS PASSED")
