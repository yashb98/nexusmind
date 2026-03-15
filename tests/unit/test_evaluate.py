"""Tests for adapter evaluation."""

from training.evaluate import evaluate_adapter


class TestEvaluateAdapter:
    def test_passes_low_variance(self) -> None:
        result = evaluate_adapter(
            "adapters/test",
            "investigator",
            test_results=[
                {
                    "openness_var": 0.1,
                    "conscientiousness_var": 0.15,
                    "extraversion_var": 0.12,
                    "agreeableness_var": 0.08,
                    "neuroticism_var": 0.11,
                }
            ],
        )
        assert result["passed"] is True
        assert result["max_variance"] < 0.5

    def test_fails_high_variance(self) -> None:
        result = evaluate_adapter(
            "adapters/test",
            "commander",
            test_results=[
                {
                    "openness_var": 0.6,
                    "conscientiousness_var": 0.7,
                    "extraversion_var": 0.8,
                    "agreeableness_var": 0.5,
                    "neuroticism_var": 0.55,
                }
            ],
        )
        assert result["passed"] is False
        assert result["max_variance"] >= 0.5
