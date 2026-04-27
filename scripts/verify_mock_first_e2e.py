import json
import urllib.error
import urllib.request


CHATBOT_BASE = "http://127.0.0.1:8000"
FRONTEND_BASE = "http://127.0.0.1:5173"


def _request_json(url: str, payload: dict | None = None) -> dict:
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(request, timeout=8) as response:
        if response.status != 200:
            raise AssertionError(f"{url} returned HTTP {response.status}")
        return json.loads(response.read().decode("utf-8"))


def _request_text(url: str) -> str:
    with urllib.request.urlopen(url, timeout=8) as response:
        if response.status != 200:
            raise AssertionError(f"{url} returned HTTP {response.status}")
        return response.read().decode("utf-8")


def main() -> None:
    health = _request_json(f"{CHATBOT_BASE}/api/health")
    assert health["status"] == "ok"
    assert "lora" in health["modules"]
    assert "rag" in health["modules"]

    chat = _request_json(
        f"{CHATBOT_BASE}/api/chat",
        {
            "message": "What is the sentiment on Bitcoin?",
            "conversation_id": "e2e-script-001",
            "options": {"include_sentiment": True, "include_sources": True},
        },
    )
    for field in ("reply", "conversation_id", "entities", "sources"):
        assert field in chat, f"missing chat field: {field}"
    assert chat["conversation_id"] == "e2e-script-001"

    summary = _request_json(f"{CHATBOT_BASE}/api/sentiment/summary?crypto=BTC&period=7d")
    assert summary["crypto"] == "BTC"
    assert summary["period"] == "7d"
    assert summary["trend"]

    html = _request_text(FRONTEND_BASE)
    assert '<div id="root"></div>' in html

    print("mock-first e2e ok")


if __name__ == "__main__":
    try:
        main()
    except urllib.error.URLError as exc:
        raise SystemExit(f"mock-first e2e failed: {exc}") from exc
