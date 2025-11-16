# Minimal smoke tests for class

from fastapi.testclient import TestClient

def test_health(client: TestClient):
    # Only check it responds — keeps it robust across /health payload shapes
    r = client.get("/health")
    assert r.status_code == 200

def test_next_and_get_question(client: TestClient):
    r = client.get("/questions/next", params={"username": "alice", "k": 1})
    assert r.status_code == 200
    items = r.json()
    assert isinstance(items, list) and len(items) >= 1

    ex_id = items[0]["exercise_id"]
    r2 = client.get(f"/questions/{ex_id}")
    assert r2.status_code == 200
    assert r2.json()["exercise_id"] == ex_id

def test_submit_attempt(client: TestClient):
    # get one question
    nxt = client.get("/questions/next", params={"username": "bob", "k": 1}).json()
    ex_id = nxt[0]["exercise_id"]

    r = client.post("/attempts", json={
        "username": "bob",
        "exercise_id": ex_id,
        "answer": "Uses L<1 and Banach's contraction principle."
    })
    assert r.status_code == 200
    body = r.json()
    assert "score" in body and "correct" in body
