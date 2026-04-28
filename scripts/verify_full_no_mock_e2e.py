import json
import os
import urllib.error
import urllib.request


CHATBOT_BASE = os.getenv("CHATBOT_BASE_URL", "http://127.0.0.1:8000")
FRONTEND_BASE = os.getenv("FRONTEND_BASE_URL", "http://127.0.0.1:5173")


def _request_json(url: str, payload: dict | None = None) -> dict:
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(request, timeout=60) as response:
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

    modules = health["modules"]
    assert modules["lora"]["status"] == "ok", modules["lora"]
    assert modules["rag"]["status"] == "ok", modules["rag"]
    assert modules["rag"].get("documents_indexed", 0) > 0, modules["rag"]

    chat = _request_json(
        f"{CHATBOT_BASE}/api/chat",
        {
            "message": "Use recent crypto reports to explain the Bitcoin market outlook.",
            "conversation_id": "full-no-mock-e2e-001",
            "options": {"include_sentiment": True, "include_sources": True},
        },
    )
    assert chat.get("reply"), "missing reply"
    assert chat.get("conversation_id") == "full-no-mock-e2e-001"
    assert chat.get("entities"), "missing entities"
    assert chat.get("sources"), "missing real RAG sources"

    sentiment = chat.get("sentiment")
    assert sentiment and sentiment.get("label"), "missing sentiment"
    assert isinstance(sentiment.get("confidence"), (int, float)), sentiment

    first_source = chat["sources"][0]
    assert first_source.get("title"), first_source
    assert first_source.get("snippet"), first_source

    summary = _request_json(f"{CHATBOT_BASE}/api/sentiment/summary?crypto=BTC&period=7d")
    assert summary["crypto"] == "BTC"
    assert summary["period"] == "7d"
    assert summary["trend"]

    html = _request_text(FRONTEND_BASE)
    assert '<div id="root"></div>' in html

    print("full no-mock e2e ok")
    print(
        json.dumps(
            {
                "rag_documents_indexed": modules["rag"]["documents_indexed"],
                "rag_collection": modules["rag"].get("collection"),
                "sentiment_label": sentiment["label"],
                "source_count": len(chat["sources"]),
                "first_source_title": first_source["title"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    try:
        main()
    except urllib.error.URLError as exc:
        raise SystemExit(f"full no-mock e2e failed: {exc}") from exc
