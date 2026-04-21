import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault("USE_MOCK", "true")

import pytest
from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)


def test_health_returns_200():
    resp = client.get("/api/health")
    assert resp.status_code == 200


def test_health_structure():
    resp = client.get("/api/health")
    data = resp.json()
    assert data["status"] == "ok"
    assert "lora" in data["modules"]
    assert "rag" in data["modules"]
    assert "ner" in data["modules"]


def test_health_ner_backend():
    resp = client.get("/api/health")
    assert resp.json()["modules"]["ner"]["status"] == "ok"
