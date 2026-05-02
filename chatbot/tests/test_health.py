import sys, os
import json
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


@pytest.mark.asyncio
async def test_real_health_degrades_when_lora_unavailable(monkeypatch):
    from src.config import settings
    from src.routes import health as health_route

    monkeypatch.setattr(settings, "use_mock", False)
    monkeypatch.setattr(settings, "lora_use_mock", False)
    monkeypatch.setattr(settings, "rag_use_mock", True)
    monkeypatch.setattr(
        health_route,
        "_probe_lora_status",
        lambda: {"status": "unavailable", "model_loaded": False, "reason": "connection_refused"},
    )

    data = await health_route.health()
    assert data["status"] == "degraded"
    assert data["modules"]["lora"]["status"] == "unavailable"
    assert data["modules"]["rag"]["status"] == "mock"


def test_rag_health_probe_reports_unavailable_without_dependency(monkeypatch):
    from src.routes import health as health_route

    class BrokenClient:
        def __init__(self, **kwargs):
            raise RuntimeError("milvus unavailable")

    monkeypatch.setattr(health_route, "_milvus_client_class", lambda: BrokenClient)
    data = health_route._probe_rag_status()
    assert data["status"] == "unavailable"
    assert data["documents_indexed"] == 0
    assert data["collection"]


def test_lora_health_probe_requires_remote_base_url(monkeypatch):
    from src.config import settings
    from src.routes import health as health_route

    monkeypatch.setattr(settings, "lora_remote_base_url", "")
    data = health_route._probe_lora_status()
    assert data["status"] == "unavailable"
    assert data["reason"] == "missing_lora_remote_base_url"
    assert data["model_loaded"] is False


def test_lora_health_probe_requires_api_key(monkeypatch):
    from src.config import settings
    from src.routes import health as health_route

    monkeypatch.setattr(settings, "lora_remote_base_url", "http://127.0.0.1:6006/v1")
    monkeypatch.setattr(settings, "lora_remote_api_key", "")
    data = health_route._probe_lora_status()
    assert data["status"] == "unavailable"
    assert data["reason"] == "missing_lora_remote_api_key"


def test_lora_health_probe_validates_required_models(monkeypatch):
    from src.config import settings
    from src.routes import health as health_route

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return json.dumps(
                {
                    "data": [
                        {"id": "llama3.1-8b-instruct"},
                        {"id": "sentiment-lora"},
                        {"id": "ift-lora"},
                    ]
                }
            ).encode("utf-8")

    def fake_urlopen(request, timeout):
        assert request.full_url == "http://127.0.0.1:6006/v1/models"
        assert request.headers["Authorization"].startswith("Bearer ")
        assert timeout == 30.0
        return FakeResponse()

    monkeypatch.setattr(settings, "lora_remote_base_url", "http://127.0.0.1:6006/v1")
    monkeypatch.setattr(settings, "lora_remote_api_key", "test-key")
    monkeypatch.setattr(settings, "lora_remote_timeout_seconds", 30.0)
    monkeypatch.setattr(health_route.urllib.request, "urlopen", fake_urlopen)

    data = health_route._probe_lora_status()
    assert data["status"] == "ok"
    assert data["model_loaded"] is True
    assert data["models"] == ["ift-lora", "sentiment-lora"]


def test_lora_health_probe_reports_missing_models(monkeypatch):
    from src.config import settings
    from src.routes import health as health_route

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return json.dumps({"data": [{"id": "sentiment-lora"}]}).encode("utf-8")

    monkeypatch.setattr(settings, "lora_remote_base_url", "http://127.0.0.1:6006/v1")
    monkeypatch.setattr(settings, "lora_remote_api_key", "test-key")
    monkeypatch.setattr(health_route.urllib.request, "urlopen", lambda request, timeout: FakeResponse())

    data = health_route._probe_lora_status()
    assert data["status"] == "unavailable"
    assert data["reason"] == "required_models_missing"
    assert data["missing_models"] == ["ift-lora"]
