"""
M21 Lab: API Test Client (COMPLETE)
====================================
Run the service first, then: API_KEY=dev-secret-123 python test_client.py
"""

import os
import sys

import httpx

BASE = os.environ.get("API_BASE", "http://localhost:8080")
KEY = os.environ.get("API_KEY", "dev-secret-123")
AUTH = {"Authorization": f"Bearer {KEY}"}


def show(label: str, resp: httpx.Response, expect: int):
    ok = "OK " if resp.status_code == expect else "FAIL"
    print(f"[{ok}] {label}: HTTP {resp.status_code} (expected {expect})")
    body = resp.text[:200]
    print(f"      {body}")
    return resp.status_code == expect


def main():
    results = []
    with httpx.Client(timeout=120) as c:
        print("1. Health check (no auth needed)")
        results.append(show("GET /health", c.get(f"{BASE}/health"), 200))

        print("\n2. Valid request")
        r = c.post(f"{BASE}/agent/run", headers=AUTH,
                   json={"query": "What is (12 * 9) + 6?"})
        results.append(show("POST /agent/run", r, 200))
        if r.status_code == 200:
            data = r.json()
            for field in ("result", "session_id", "iterations", "latency_ms", "model"):
                assert field in data, f"missing contract field: {field}"
            print(f"      contract fields present; result: {data['result'][:80]}")

        print("\n3. Missing token")
        results.append(show("no auth header",
                            c.post(f"{BASE}/agent/run", json={"query": "hi"}), 401))

        print("\n4. Wrong token")
        results.append(show("bad token",
                            c.post(f"{BASE}/agent/run",
                                   headers={"Authorization": "Bearer wrong"},
                                   json={"query": "hi"}), 401))

        print("\n5. Malformed body (empty query — Pydantic rejects before your code runs)")
        results.append(show("empty query",
                            c.post(f"{BASE}/agent/run", headers=AUTH,
                                   json={"query": "   "}), 422))

    print(f"\n{'ALL TESTS PASSED' if all(results) else 'SOME TESTS FAILED'}")
    sys.exit(0 if all(results) else 1)


if __name__ == "__main__":
    main()
