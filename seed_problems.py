"""
Seeds 5 well-structured problems into DevMentor, each with a proper
input/output format, constraints, and multiple test cases (sample +
hidden). All test cases hand-verified before inclusion.

Usage:
    python3 seed_problems.py <admin_username> <admin_password>
"""
import sys
import requests

requests.packages.urllib3.disable_warnings()  # self-signed cert locally

API = "https://localhost/api"


def login(username, password):
    resp = requests.post(
        f"{API}/auth/login", data={"username": username, "password": password}, verify=False
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def create_problem(token, slug, title, statement):
    resp = requests.post(
        f"{API}/problems",
        headers={"Authorization": f"Bearer {token}"},
        json={"slug": slug, "title": title, "statement": statement},
        verify=False,
    )
    if resp.status_code == 400:
        print(f"  (problem already exists, skipping) {slug}")
        return
    resp.raise_for_status()
    print(f"  created problem: {slug}")


def add_test_case(token, slug, stdin, expected_output, is_sample):
    resp = requests.post(
        f"{API}/problems/{slug}/test-cases",
        headers={"Authorization": f"Bearer {token}"},
        json={"stdin": stdin, "expected_output": expected_output, "is_sample": is_sample},
        verify=False,
    )
    resp.raise_for_status()
    print(f"    added test case (sample={is_sample})")


PROBLEMS = [
    {
        "slug": "two-sum",
        "title": "Two Sum",
        "statement": (
            "Given an array of integers and a target value, return the indices of the "
            "two numbers whose values add up to the target.\n\n"
            "You may assume each input has exactly one valid answer, and you may not "
            "use the same element twice.\n\n"
            "Input Format:\n"
            "Line 1: space-separated integers -- the array (nums)\n"
            "Line 2: a single integer -- the target\n\n"
            "Output Format:\n"
            "Print the two 0-based indices of the numbers that sum to the target, "
            "space-separated, in the order they appear in the array (smaller index first).\n\n"
            "Constraints:\n"
            "2 <= length of nums <= 1000\n"
            "-1000000 <= nums[i] <= 1000000\n"
            "-1000000 <= target <= 1000000\n"
            "Exactly one valid answer exists for each input.\n\n"
            "Example:\nInput:\n2 7 11 15\n9\n\nOutput:\n0 1\n\n"
            "Explanation:\nnums[0] + nums[1] = 2 + 7 = 9, so the answer is indices 0 and 1."
        ),
        "test_cases": [
            {"stdin": "2 7 11 15\n9", "expected_output": "0 1", "is_sample": True},
            {"stdin": "1 2 3 4 5\n8", "expected_output": "2 4", "is_sample": False},
            {"stdin": "3 3\n6", "expected_output": "0 1", "is_sample": False},
        ],
    },
    {
        "slug": "fizzbuzz",
        "title": "FizzBuzz",
        "statement": (
            "Given an integer N, print the numbers from 1 to N, one per line. "
            'For multiples of 3, print "Fizz" instead of the number. For multiples '
            'of 5, print "Buzz" instead. For multiples of both 3 and 5, print '
            '"FizzBuzz".\n\n'
            "Input Format:\nA single integer N.\n\n"
            "Output Format:\nN lines, one value per line, following the rules above.\n\n"
            "Constraints:\n1 <= N <= 10000\n\n"
            "Example:\nInput:\n15\n\n"
            "Output:\n1\n2\nFizz\n4\nBuzz\nFizz\n7\n8\nFizz\nBuzz\n11\nFizz\n13\n14\nFizzBuzz"
        ),
        "test_cases": [
            {
                "stdin": "15",
                "expected_output": "1\n2\nFizz\n4\nBuzz\nFizz\n7\n8\nFizz\nBuzz\n11\nFizz\n13\n14\nFizzBuzz",
                "is_sample": True,
            },
            {"stdin": "5", "expected_output": "1\n2\nFizz\n4\nBuzz", "is_sample": False},
            {"stdin": "1", "expected_output": "1", "is_sample": False},
        ],
    },
    {
        "slug": "palindrome-check",
        "title": "Palindrome Check",
        "statement": (
            "Given a string, determine whether it reads the same forwards and backwards.\n\n"
            "Input Format:\nA single line containing the string (letters only, no spaces).\n\n"
            "Output Format:\nPrint YES if the string is a palindrome, otherwise print NO. "
            "Comparison is case-sensitive.\n\n"
            "Constraints:\n1 <= length of string <= 10000\n\n"
            "Example:\nInput:\nracecar\n\nOutput:\nYES"
        ),
        "test_cases": [
            {"stdin": "racecar", "expected_output": "YES", "is_sample": True},
            {"stdin": "hello", "expected_output": "NO", "is_sample": False},
            {"stdin": "a", "expected_output": "YES", "is_sample": False},
        ],
    },
    {
        "slug": "binary-search",
        "title": "Binary Search",
        "statement": (
            "Given a sorted array of distinct integers and a target value, return the "
            "index of the target if it exists in the array, otherwise return -1.\n\n"
            "Input Format:\n"
            "Line 1: space-separated integers, sorted ascending -- the array\n"
            "Line 2: a single integer -- the target\n\n"
            "Output Format:\nPrint the 0-based index of the target, or -1 if not found.\n\n"
            "Constraints:\n"
            "1 <= length of array <= 100000\n"
            "Array is sorted in ascending order with no duplicate values.\n\n"
            "Example:\nInput:\n1 3 5 7 9 11\n7\n\nOutput:\n3"
        ),
        "test_cases": [
            {"stdin": "1 3 5 7 9 11\n7", "expected_output": "3", "is_sample": True},
            {"stdin": "1 3 5 7 9 11\n4", "expected_output": "-1", "is_sample": False},
            {"stdin": "5\n5", "expected_output": "0", "is_sample": False},
        ],
    },
    {
        "slug": "maximum-subarray",
        "title": "Maximum Subarray",
        "statement": (
            "Given an array of integers (which may include negative numbers), find the "
            "contiguous subarray (containing at least one number) with the largest sum, "
            "and print that sum.\n\n"
            "Input Format:\nA single line of space-separated integers.\n\n"
            "Output Format:\nPrint a single integer -- the maximum subarray sum.\n\n"
            "Constraints:\n"
            "1 <= length of array <= 100000\n"
            "-100000 <= nums[i] <= 100000\n\n"
            "Example:\nInput:\n-2 1 -3 4 -1 2 1 -5 4\n\nOutput:\n6\n\n"
            "Explanation:\nThe subarray [4, -1, 2, 1] has the largest sum = 6."
        ),
        "test_cases": [
            {"stdin": "-2 1 -3 4 -1 2 1 -5 4", "expected_output": "6", "is_sample": True},
            {"stdin": "1 2 3 4 5", "expected_output": "15", "is_sample": False},
            {"stdin": "-5 -4 -3", "expected_output": "-3", "is_sample": False},
        ],
    },
]


def main():
    if len(sys.argv) != 3:
        print("Usage: python3 seed_problems.py <username> <password>")
        sys.exit(1)

    username, password = sys.argv[1], sys.argv[2]
    token = login(username, password)
    print(f"Logged in as {username}\n")

    for problem in PROBLEMS:
        print(f"Creating: {problem['title']}")
        create_problem(token, problem["slug"], problem["title"], problem["statement"])
        for tc in problem["test_cases"]:
            add_test_case(token, problem["slug"], tc["stdin"], tc["expected_output"], tc["is_sample"])
        print()

    print("Done -- 5 problems seeded.")


if __name__ == "__main__":
    main()
