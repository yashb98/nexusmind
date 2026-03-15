"""Tests for verification council — scoring, judge decisions."""

from src.services.verification import (
    _parse_judge_response,
    _parse_score_response,
)


class TestParseScoreResponse:
    def test_valid_json(self) -> None:
        resp = '{"score": 0.85, "reasoning": "Reliable source"}'
        result = _parse_score_response(resp)
        assert result["score"] == 0.85
        assert "Reliable" in result["reasoning"]

    def test_score_clamped(self) -> None:
        resp = '{"score": 1.5, "reasoning": "test"}'
        result = _parse_score_response(resp)
        assert result["score"] == 1.0

    def test_invalid_returns_default(self) -> None:
        result = _parse_score_response("not json", default_score=0.3)
        assert result["score"] == 0.3

    def test_with_markdown(self) -> None:
        resp = '```json\n{"score": 0.7, "reasoning": "ok"}\n```'
        result = _parse_score_response(resp)
        assert result["score"] == 0.7


class TestParseJudgeResponse:
    def test_accepted(self) -> None:
        resp = '{"decision": "accepted", "reasoning": "High quality"}'
        result = _parse_judge_response(resp)
        assert result["decision"] == "accepted"

    def test_rejected(self) -> None:
        resp = '{"decision": "rejected", "reasoning": "Unreliable"}'
        result = _parse_judge_response(resp)
        assert result["decision"] == "rejected"

    def test_invalid_decision_defaults_provisional(self) -> None:
        resp = '{"decision": "maybe", "reasoning": "unclear"}'
        result = _parse_judge_response(resp)
        assert result["decision"] == "provisional"

    def test_parse_failure_defaults_provisional(self) -> None:
        result = _parse_judge_response("garbage")
        assert result["decision"] == "provisional"

    def test_all_valid_decisions(self) -> None:
        for decision in ["accepted", "provisional", "investigate", "rejected"]:
            resp = f'{{"decision": "{decision}", "reasoning": "test"}}'
            result = _parse_judge_response(resp)
            assert result["decision"] == decision
