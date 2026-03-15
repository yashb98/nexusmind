"""Tests for fact/pattern separation in training data."""

from training.prepare_data import strip_facts


class TestStripFacts:
    def test_removes_dates(self) -> None:
        text = "On 2025-03-15, something happened."
        result = strip_facts(text)
        assert "2025-03-15" not in result
        assert "[FACT]" in result

    def test_removes_urls(self) -> None:
        text = "Check out https://example.com/page for details."
        result = strip_facts(text)
        assert "https://example.com" not in result

    def test_removes_percentages(self) -> None:
        text = "Accuracy improved by 15.5% over baseline."
        result = strip_facts(text)
        assert "15.5%" not in result

    def test_removes_dollar_amounts(self) -> None:
        text = "The cost was $1,234.56 per unit."
        result = strip_facts(text)
        assert "$1,234.56" not in result

    def test_preserves_personality_language(self) -> None:
        text = "I find that approach quite interesting and worth exploring further."
        result = strip_facts(text)
        assert result == text  # No facts to strip

    def test_preserves_socratic_questions(self) -> None:
        text = "What makes you think that's the right approach?"
        result = strip_facts(text)
        assert result == text
