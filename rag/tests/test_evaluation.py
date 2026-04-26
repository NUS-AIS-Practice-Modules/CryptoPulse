import unittest

from src.evaluation.faithfulness import (
    FaithfulnessCase,
    faithfulness_score,
    run_faithfulness_eval,
)
from src.retrieval.retrieval import RetrievedDocument, RetrievalResult


class EvaluationTests(unittest.TestCase):
    def test_faithfulness_score_measures_context_support(self) -> None:
        score = faithfulness_score(
            "MiCA regulates crypto asset service providers.",
            "MiCA regulates crypto asset service providers and issuers.",
        )

        self.assertGreaterEqual(score, 0.8)

    def test_run_faithfulness_eval_uses_retriever_results(self) -> None:
        def fake_retriever(query, top_k=5, source_filter=None):
            return RetrievalResult(
                query=query,
                documents=[
                    RetrievedDocument(
                        title="Aave V3",
                        content="Aave improves capital efficiency with isolation mode.",
                        source="whitepaper",
                        relevance_score=1.0,
                        metadata={"source_id": "aave-v3"},
                    )
                ],
                total_candidates=1,
                retrieval_time_ms=2.0,
            )

        payload = run_faithfulness_eval(
            [
                FaithfulnessCase(
                    query="Aave",
                    grounded_answer="Aave improves capital efficiency.",
                )
            ],
            retriever=fake_retriever,
        )

        self.assertEqual(payload["case_count"], 1)
        self.assertGreaterEqual(payload["generation_faithfulness"], 0.85)
        self.assertEqual(payload["average_retrieval_time_ms"], 2.0)


if __name__ == "__main__":
    unittest.main()
