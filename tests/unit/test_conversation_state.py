"""Tests for conversation state transitions and phase progression."""

from src.services.conversation import PHASE_MAP, _evaluate_turn


class TestPhaseProgression:
    def test_phase_map_covers_all_turns(self) -> None:
        for turn in range(1, 11):
            assert turn in PHASE_MAP

    def test_open_phase(self) -> None:
        assert PHASE_MAP[1] == "OPEN"
        assert PHASE_MAP[2] == "OPEN"

    def test_probe_phase(self) -> None:
        assert PHASE_MAP[3] == "PROBE"
        assert PHASE_MAP[4] == "PROBE"

    def test_deepen_phase(self) -> None:
        assert PHASE_MAP[5] == "DEEPEN"
        assert PHASE_MAP[6] == "DEEPEN"

    def test_challenge_phase(self) -> None:
        assert PHASE_MAP[7] == "CHALLENGE"
        assert PHASE_MAP[8] == "CHALLENGE"

    def test_synthesize_phase(self) -> None:
        assert PHASE_MAP[9] == "SYNTHESIZE"

    def test_extract_phase(self) -> None:
        assert PHASE_MAP[10] == "EXTRACT"


class TestEvaluateTurn:
    def test_continues_when_under_max(self) -> None:
        state = {
            "turn_count": 5,
            "max_turns": 10,
            "should_continue": True,
        }
        result = _evaluate_turn(state)
        assert result["should_continue"] is True

    def test_stops_at_max_turns(self) -> None:
        state = {
            "turn_count": 10,
            "max_turns": 10,
            "should_continue": True,
        }
        result = _evaluate_turn(state)
        assert result["should_continue"] is False
