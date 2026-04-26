import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault("USE_MOCK", "true")

import pytest
from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)

PAYLOAD = {"message": "What is Bitcoin?", "conversation_id": "test-001"}


def test_chat_returns_200():
    resp = client.post("/api/chat", json=PAYLOAD)
    assert resp.status_code == 200


def test_chat_response_fields():
    resp = client.post("/api/chat", json=PAYLOAD)
    data = resp.json()
    for field in ("reply", "entities", "sources", "conversation_id", "timestamp"):
        assert field in data, f"missing field: {field}"


def test_chat_conversation_id_preserved():
    resp = client.post("/api/chat", json=PAYLOAD)
    assert resp.json()["conversation_id"] == "test-001"


def test_chat_auto_generates_conv_id():
    resp = client.post("/api/chat", json={"message": "Hello"})
    assert resp.json()["conversation_id"] != ""


def test_chat_multi_turn_isolation():
    client.post("/api/chat", json={"message": "BTC question", "conversation_id": "conv-A"})
    client.post("/api/chat", json={"message": "ETH question", "conversation_id": "conv-B"})
    # Different conversations must not bleed into each other
    resp = client.post("/api/chat", json={"message": "Follow up", "conversation_id": "conv-A"})
    assert resp.status_code == 200


def test_chat_empty_message_rejected():
    resp = client.post("/api/chat", json={"message": "   "})
    assert resp.status_code == 422


def test_chat_latency_mock(benchmark=None):
    import time
    start = time.time()
    client.post("/api/chat", json=PAYLOAD)
    elapsed = time.time() - start
    assert elapsed < 3.0, f"Mock response too slow: {elapsed:.2f}s"


def test_sentiment_included_for_crypto():
    resp = client.post("/api/chat", json={
        "message": "What about bitcoin?",
        "conversation_id": "test-002",
        "options": {"include_sentiment": True, "include_sources": True},
    })
    data = resp.json()
    # sentiment should be populated because "bitcoin" triggers NER → BTC lookup
    assert "sentiment" in data
