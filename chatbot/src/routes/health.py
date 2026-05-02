import os
import json
import urllib.error
import urllib.request

from fastapi import APIRouter
from src.config import settings

router = APIRouter()


@router.get("/api/health")
async def health():
    lora_status = {"status": "mock", "model_loaded": False}
    rag_status = {"status": "mock", "documents_indexed": 0}
    ner_status = {"status": "ok", "backend": settings.ner_backend}

    if not settings.use_mock:
        lora_status = (
            {"status": "mock", "model_loaded": False}
            if settings.lora_use_mock
            else _probe_lora_status()
        )
        rag_status = (
            {"status": "mock", "documents_indexed": 0}
            if settings.rag_use_mock
            else _probe_rag_status()
        )

    overall_status = _overall_status([lora_status, rag_status, ner_status])

    return {
        "status": overall_status,
        "modules": {
            "lora": lora_status,
            "rag": rag_status,
            "ner": ner_status,
        },
    }


def _overall_status(modules: list[dict]) -> str:
    if any(module.get("status") in {"unavailable", "down"} for module in modules):
        return "degraded"
    return "ok"


def _probe_lora_status() -> dict:
    base_url = settings.lora_remote_base_url.rstrip("/")
    required_models = {settings.lora_sentiment_model, settings.lora_chat_model}

    if not base_url:
        return {
            "status": "unavailable",
            "model_loaded": False,
            "reason": "missing_lora_remote_base_url",
            "required_models": sorted(required_models),
        }
    if not settings.lora_remote_api_key:
        return {
            "status": "unavailable",
            "model_loaded": False,
            "endpoint": f"{base_url}/models",
            "reason": "missing_lora_remote_api_key",
            "required_models": sorted(required_models),
        }

    request = urllib.request.Request(
        f"{base_url}/models",
        headers={"Authorization": f"Bearer {settings.lora_remote_api_key}"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=settings.lora_remote_timeout_seconds) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return {
            "status": "unavailable",
            "model_loaded": False,
            "endpoint": f"{base_url}/models",
            "reason": f"http_{exc.code}",
            "required_models": sorted(required_models),
        }
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
        return {
            "status": "unavailable",
            "model_loaded": False,
            "endpoint": f"{base_url}/models",
            "reason": str(exc),
            "required_models": sorted(required_models),
        }

    available_models = {
        str(item.get("id"))
        for item in payload.get("data", [])
        if isinstance(item, dict) and item.get("id")
    }
    missing_models = sorted(required_models - available_models)
    if missing_models:
        return {
            "status": "unavailable",
            "model_loaded": False,
            "endpoint": f"{base_url}/models",
            "reason": "required_models_missing",
            "required_models": sorted(required_models),
            "available_models": sorted(available_models),
            "missing_models": missing_models,
        }

    return {
        "status": "ok",
        "model_loaded": True,
        "endpoint": f"{base_url}/models",
        "models": sorted(required_models),
    }


def _probe_rag_status() -> dict:
    collection_name = os.getenv("MILVUS_COLLECTION", "cryptopulse_rag_chunks")
    uri = os.getenv("MILVUS_URI", "http://127.0.0.1:19530")
    token = os.getenv("MILVUS_TOKEN", "")

    try:
        MilvusClient = _milvus_client_class()
        kwargs = {"uri": uri}
        if token:
            kwargs["token"] = token
        client = MilvusClient(**kwargs)
        if not client.has_collection(collection_name):
            return {
                "status": "unavailable",
                "documents_indexed": 0,
                "collection": collection_name,
                "reason": "collection_not_found",
            }
        stats = client.get_collection_stats(collection_name)
        row_count = int(stats.get("row_count", 0))
        return {
            "status": "ok",
            "documents_indexed": row_count,
            "collection": collection_name,
        }
    except Exception as exc:
        return {
            "status": "unavailable",
            "documents_indexed": 0,
            "collection": collection_name,
            "reason": str(exc),
        }


def _milvus_client_class():
    from pymilvus import MilvusClient

    return MilvusClient
