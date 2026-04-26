from __future__ import annotations

import argparse
import json
import time
from dataclasses import asdict, dataclass
from typing import Any

from src.retrieval import retrieve


@dataclass(frozen=True)
class BenchmarkCase:
    query: str
    expected_source_id_contains: str
    source_filter: list[str] | None = None


DEFAULT_CASES = [
    BenchmarkCase("Aave V3 capital efficiency", "aave-v3-technical-paper"),
    BenchmarkCase("MiCA crypto asset service providers", "the-road-to-crypto-regulation", ["regulatory"]),
    BenchmarkCase("Binance plea agreement criminal case", "binance", ["case_study"]),
    BenchmarkCase("CoinShares weekly fund flows March 2026", "fund-flows", ["news"]),
]


def run_benchmark(cases: list[BenchmarkCase] | None = None, *, top_k: int = 5) -> dict[str, Any]:
    benchmark_cases = cases or DEFAULT_CASES
    results = []
    hits = 0
    started = time.perf_counter()
    for case in benchmark_cases:
        result = retrieve(case.query, top_k=top_k, source_filter=case.source_filter)
        source_ids = [
            str(document.metadata.get("source_id", "")).lower()
            for document in result.documents
        ]
        matched = any(case.expected_source_id_contains in source_id for source_id in source_ids)
        hits += int(matched)
        results.append(
            {
                **asdict(case),
                "matched": matched,
                "retrieval_time_ms": result.retrieval_time_ms,
                "returned_source_ids": source_ids,
            }
        )

    recall = hits / len(benchmark_cases) if benchmark_cases else 0.0
    return {
        "case_count": len(benchmark_cases),
        "recall_at_k": recall,
        "top_k": top_k,
        "average_retrieval_time_ms": sum(item["retrieval_time_ms"] for item in results)
        / max(len(results), 1),
        "wall_time_ms": (time.perf_counter() - started) * 1000,
        "results": results,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run RAG retrieval benchmark cases.")
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args(argv)
    print(json.dumps(run_benchmark(top_k=args.top_k), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
