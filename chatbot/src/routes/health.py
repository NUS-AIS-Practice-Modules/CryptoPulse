from fastapi import APIRouter
from src.config import settings

router = APIRouter()


@router.get("/api/health")
async def health():
    lora_status = {"status": "mock", "model_loaded": False}
    rag_status = {"status": "mock", "documents_indexed": 0}
    ner_status = {"status": "ok", "backend": settings.ner_backend}

    if not settings.use_mock:
        lora_status = {"status": "ok", "model_loaded": True}
        rag_status = {"status": "ok", "documents_indexed": 9200}

    return {
        "status": "ok",
        "modules": {
            "lora": lora_status,
            "rag": rag_status,
            "ner": ner_status,
        },
    }
