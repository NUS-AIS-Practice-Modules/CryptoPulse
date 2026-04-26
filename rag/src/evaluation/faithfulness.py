from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from typing import Any, Callable

from src.retrieval import retrieve

try:
    from shared.types import RetrievalResult
except ImportError:
    from src.retrieval.retrieval import RetrievalResult


TOKEN_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9$%-]*")
STOPWORDS = {
    "and",
    "are",
    "for",
    "from",
    "into",
    "that",
    "the",
    "their",
    "this",
    "through",
    "with",
}


@dataclass(frozen=True)
class FaithfulnessCase:
    query: str
    grounded_answer: str
    source_filter: list[str] | None = None


DEFAULT_CASES = [
    FaithfulnessCase(
        query="Aave V3 capital efficiency",
        grounded_answer="Aave capital efficiency",
    ),
    FaithfulnessCase(
        query="MiCA crypto asset service providers",
        grounded_answer="MiCA crypto asset",
        source_filter=["regulatory"],
    ),
    FaithfulnessCase(
        query="Binance plea agreement criminal case",
        grounded_answer="Binance plea agreement",
        source_filter=["case_study"],
    ),
    FaithfulnessCase(
        query="CoinShares weekly fund flows March 2026",
        grounded_answer="CoinShares fund flows",
        source_filter=["news"],
    ),
]


Retriever = Callable[[str, int, list[str] | None], RetrievalResult]


def run_faithfulness_eval(
    cases: list[FaithfulnessCase] | None = None,
    *,
    top_k: int = 5,
    retriever: Retriever = retrieve,
) -> dict[str, Any]:
    eval_cases = cases or DEFAULT_CASES
    results = []
    for case in eval_cases:
        retrieval = retriever(case.query, top_k, case.source_filter)
        context = "\n".join(
            f"{document.title}\n{document.content}" for document in retrieval.documents
        )
        score = faithfulness_score(case.grounded_answer, context)
        results.append(
            {
                **asdict(case),
                "faithfulness": score,
                "retrieval_time_ms": retrieval.retrieval_time_ms,
                "document_count": len(retrieval.documents),
            }
        )

    average = sum(item["faithfulness"] for item in results) / max(len(results), 1)
    return {
        "case_count": len(eval_cases),
        "top_k": top_k,
        "generation_faithfulness": average,
        "average_retrieval_time_ms": sum(item["retrieval_time_ms"] for item in results)
        / max(len(results), 1),
        "results": results,
    }


def faithfulness_score(answer: str, context: str) -> float:
    answer_tokens = _content_tokens(answer)
    if not answer_tokens:
        return 0.0
    context_tokens = set(_content_tokens(context))
    supported = sum(1 for token in answer_tokens if token in context_tokens)
    return supported / len(answer_tokens)


def _content_tokens(text: str) -> list[str]:
    return [
        match.group(0).lower()
        for match in TOKEN_PATTERN.finditer(text)
        if len(match.group(0)) >= 3 and match.group(0).lower() not in STOPWORDS
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run RAG grounded-answer faithfulness checks.")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--min-score", type=float, default=0.85)
    args = parser.parse_args(argv)
    payload = run_faithfulness_eval(top_k=args.top_k)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["generation_faithfulness"] >= args.min_score else 1


if __name__ == "__main__":
    raise SystemExit(main())
