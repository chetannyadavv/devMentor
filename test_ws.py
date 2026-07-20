"""
Run on the HOST (not inside a container), against the api's exposed
port 8000. Needs: pip install websockets requests

Usage: python3 test_ws.py YOUR_TOKEN
"""
import asyncio
import json
import sys
import time

import requests
import websockets

TOKEN = sys.argv[1]
API = "http://localhost:8000"
WS = "ws://localhost:8000"


async def main():
    # 1. Submit
    resp = requests.post(
        f"{API}/submissions",
        headers={"Authorization": f"Bearer {TOKEN}"},
        json={
            "problem_slug": "two-sum",
            "language": "python",
            "source_code": (
                "nums=list(map(int,input().split()))\n"
                "target=int(input())\n"
                "for i in range(len(nums)):\n"
                "    for j in range(i+1,len(nums)):\n"
                "        if nums[i]+nums[j]==target:\n"
                "            print(i,j)"
            ),
        },
    )
    resp.raise_for_status()
    submission = resp.json()
    submission_id = submission["id"]
    print("Submitted:", submission_id, "verdict:", submission["overall_verdict"])

    # 2. Connect and wait for the PUSHED result -- no polling loop here.
    start = time.monotonic()
    uri = f"{WS}/ws/submissions/{submission_id}?token={TOKEN}"
    async with websockets.connect(uri) as ws:
        message = await asyncio.wait_for(ws.recv(), timeout=15)
        elapsed = time.monotonic() - start
        data = json.loads(message)
        print(f"Received via WebSocket after {elapsed:.2f}s (no polling):", data)
        assert data["overall_verdict"] == "ACCEPTED"
        print("\nWEBSOCKET TEST PASSED")


if __name__ == "__main__":
    asyncio.run(main())
