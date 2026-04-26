from typing import Any

__all__ = ["BenchmarkCase", "FaithfulnessCase", "run_benchmark", "run_faithfulness_eval"]


def __getattr__(name: str) -> Any:
    if name in {"BenchmarkCase", "run_benchmark"}:
        from .benchmark import BenchmarkCase, run_benchmark

        return {"BenchmarkCase": BenchmarkCase, "run_benchmark": run_benchmark}[name]
    if name in {"FaithfulnessCase", "run_faithfulness_eval"}:
        from .faithfulness import FaithfulnessCase, run_faithfulness_eval

        return {
            "FaithfulnessCase": FaithfulnessCase,
            "run_faithfulness_eval": run_faithfulness_eval,
        }[name]
    raise AttributeError(name)
