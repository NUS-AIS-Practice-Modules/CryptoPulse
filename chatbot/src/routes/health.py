import os

from fastapi import APIRouter
from src.config import settings

router = APIRouter()


@router.get("/api/health")
async def health():
    lora_status = {"status": "mock", "model_loaded": False}
    rag_status = {"status": "mock", "documents_indexed": 0}
    ner_status = {"status": "ok", "backend": settings.ner_backend}

    if not settings.use_mock:
        lora_status = {
            "status": "mock" if settings.lora_use_mock else "ok",
            "model_loaded": not settings.lora_use_mock,
        }
        rag_status = (
            {"status": "mock", "documents_indexed": 0}
            if settings.rag_use_mock
            else _probe_rag_status()
        )

    return {
        "status": "ok",
        "modules": {
            "lora": lora_status,
            "rag": rag_status,
            "ner": ner_status,
        },
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
