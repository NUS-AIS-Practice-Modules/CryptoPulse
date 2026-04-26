from src.mock.mock_data import MOCK_RAG_CONTEXT, MOCK_SOURCES


def get_context_for_llm(query: str, max_tokens: int = 2000, top_k: int = 5) -> str:
    return MOCK_RAG_CONTEXT.strip()


def retrieve(query: str, top_k: int = 5, source_filter: list[str] | None = None) -> dict:
    return {
        "query": query,
        "documents": MOCK_SOURCES,
        "total_candidates": len(MOCK_SOURCES),
        "retrieval_time_ms": 1.0,
    }
