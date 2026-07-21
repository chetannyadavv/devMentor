"""
The one piece of coverage we only ever verified by hand tonight: a real
submission going through the actual running stack (API -> Redis ->
judge-worker -> sandbox -> Postgres -> API), via real HTTP, not a direct
function call.

Requires the full docker-compose stack to be up:
    docker compose up -d

Registers its own throwaway user each run, rather than depending on
'bob' or any other manually-created account existing.
"""
import time
import uuid

import pytest
import requests

API = "http://localhost:8000"


@pytest.fixture
def auth_token():
    username = f"pytest_{uuid.uuid4().hex[:8]}"
    resp = requests.post(
        f"{API}/auth/register",
        json={"username": username, "email": f"{username}@example.com", "password": "testpass123"},
    )
    resp.raise_for_status()

    resp = requests.post(f"{API}/auth/login", data={"username": username, "password": "testpass123"})
    resp.raise_for_status()
    return resp.json()["access_token"]


def _poll_until_resolved(submission_id, token, timeout_seconds=15):
    headers = {"Authorization": f"Bearer {token}"}
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        resp = requests.get(f"{API}/submissions/{submission_id}", headers=headers)
        resp.raise_for_status()
        data = resp.json()
        if data["overall_verdict"] is not None:
            return data
        time.sleep(0.5)
    pytest.fail(f"submission {submission_id} did not resolve within {timeout_seconds}s")


@pytest.mark.integration
def test_submission_flow_accepted(auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    code = (
        "nums=list(map(int,input().split()))\n"
        "target=int(input())\n"
        "for i in range(len(nums)):\n"
        "    for j in range(i+1,len(nums)):\n"
        "        if nums[i]+nums[j]==target:\n"
        "            print(i,j)"
    )

    resp = requests.post(
        f"{API}/submissions",
        headers=headers,
        json={"problem_slug": "two-sum", "language": "python", "source_code": code},
    )
    resp.raise_for_status()
    submission = resp.json()
    assert submission["overall_verdict"] is None  # pending -- proves it returned immediately

    result = _poll_until_resolved(submission["id"], auth_token)
    assert result["overall_verdict"] == "ACCEPTED"
    assert len(result["test_case_results"]) > 0
    assert all(tc["verdict"] == "ACCEPTED" for tc in result["test_case_results"])


@pytest.mark.integration
def test_submission_flow_wrong_answer(auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}

    resp = requests.post(
        f"{API}/submissions",
        headers=headers,
        json={"problem_slug": "two-sum", "language": "python", "source_code": "print('wrong')"},
    )
    resp.raise_for_status()
    submission = resp.json()

    result = _poll_until_resolved(submission["id"], auth_token)
    assert result["overall_verdict"] == "FAILED"
    assert len(result["test_case_results"]) > 0
    assert all(tc["verdict"] == "WRONG_ANSWER" for tc in result["test_case_results"])
