import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.services import chat_service


@pytest.mark.asyncio
async def test_lora_real_mode_can_use_mock_rag(monkeypatch):
    monkeypatch.setattr(chat_service.settings, "use_mock", False)
    monkeypatch.setattr(chat_service.settings, "rag_use_mock", True)
    monkeypatch.setattr(chat_service.settings, "llm_backend", "lora")
    monkeypatch.setattr(chat_service.settings, "lora_use_mock", True)

    result = await chat_service.handle_chat(
        message="BTC is rallying after ETF inflows",
        conversation_id="real-lora-isolated-test",
        include_sentiment=True,
        include_sources=True,
    )

    assert result["reply"]
    assert result["sentiment"]["label"] == "Bullish"
    assert result["sources"]
