"""Smoke tests for the Hindsight API — exercised in DEMO_MODE so they run
offline, deterministically, and without any Cognee credentials (ideal for CI).

They assert the full memory lifecycle wires end to end:
remember -> graph grows -> memories listed -> recall answers ->
improve (feedback) -> enrich (Memify) -> forget -> graph shrinks.
"""

import os

import pytest

# Force the zero-key in-memory mode before the app imports its client.
os.environ["DEMO_MODE"] = "true"

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

client = TestClient(app)


@pytest.fixture(autouse=True)
def _clean_memory():
    """Start each test from an empty graph."""
    client.post("/api/forget", json={"all": True})
    yield


def test_health_reports_demo_mode():
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["mode"] == "demo"


def test_remember_grows_the_graph_and_lists_a_memory():
    r = client.post("/api/remember", json={"data": "Ada Lovelace wrote the first algorithm."})
    assert r.status_code == 200
    assert r.json()["nodes_added"] >= 1

    graph = client.get("/api/graph").json()
    assert len(graph["nodes"]) >= 1

    memories = client.get("/api/memories").json()["memories"]
    assert len(memories) == 1
    assert "Ada Lovelace" in memories[0]["label"]


def test_recall_answers_from_memory():
    client.post("/api/remember", json={"data": "The Eiffel Tower is located in Paris, France."})
    r = client.post("/api/recall", json={"query": "Where is the Eiffel Tower?"})
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert "Paris" in body["answer"]
    assert body["sources"]


def test_improve_feedback_is_accepted():
    r = client.post(
        "/api/improve",
        json={"query": "q", "answer": "a", "vote": "up", "note": "good"},
    )
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_enrich_memify_is_accepted():
    r = client.post("/api/improve/enrich", json={})
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_forget_shrinks_the_graph():
    client.post("/api/remember", json={"data": "Temporary note about Vegas."})
    before = len(client.get("/api/graph").json()["nodes"])
    assert before >= 1

    r = client.post("/api/forget", json={"all": True})
    assert r.status_code == 200

    after = len(client.get("/api/graph").json()["nodes"])
    assert after == 0
    assert after < before
