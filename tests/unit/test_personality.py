"""Tests for personality service — scoring, archetypes, prompts, compatibility."""

from src.models.onboarding import BigFiveScores, ScenarioAnswer
from src.services.personality import (
    assign_archetype,
    compute_communication_style,
    compute_compatibility,
    compute_personality_result,
    generate_description,
    generate_system_prompt,
    get_scenarios,
    score_personality,
)


class TestGetScenarios:
    def test_returns_10_questions(self) -> None:
        scenarios = get_scenarios()
        assert len(scenarios) == 10

    def test_each_has_4_options(self) -> None:
        for q in get_scenarios():
            assert len(q.options) == 4

    def test_unique_ids(self) -> None:
        ids = [q.id for q in get_scenarios()]
        assert len(set(ids)) == 10


class TestScorePersonality:
    def test_all_first_options(self) -> None:
        answers = [ScenarioAnswer(question_id=i, option_index=0) for i in range(1, 11)]
        scores = score_personality(answers)
        assert 0 <= scores.openness <= 1
        assert 0 <= scores.conscientiousness <= 1
        assert 0 <= scores.extraversion <= 1
        assert 0 <= scores.agreeableness <= 1
        assert 0 <= scores.neuroticism <= 1

    def test_neutral_baseline(self) -> None:
        """With balanced answers, scores should be near 0.5."""
        # Mix of options that roughly cancel out
        answers = [ScenarioAnswer(question_id=i, option_index=i % 4) for i in range(1, 11)]
        scores = score_personality(answers)
        for val in [
            scores.openness,
            scores.conscientiousness,
            scores.extraversion,
            scores.agreeableness,
            scores.neuroticism,
        ]:
            assert 0.0 <= val <= 1.0  # Should be valid

    def test_invalid_question_id_ignored(self) -> None:
        answers = [ScenarioAnswer(question_id=i, option_index=0) for i in range(1, 11)]
        answers[0] = ScenarioAnswer(question_id=999, option_index=0)
        scores = score_personality(answers)
        assert 0 <= scores.openness <= 1


class TestCommunicationStyle:
    def test_analytical(self) -> None:
        scores = BigFiveScores(
            openness=0.7,
            conscientiousness=0.8,
            extraversion=0.3,
            agreeableness=0.4,
            neuroticism=0.3,
        )
        assert compute_communication_style(scores) == "analytical"

    def test_driver(self) -> None:
        # assertive = E + (1-A) = 0.6+0.8 = 1.4 >= 1
        # responsive = A + E = 0.2+0.6 = 0.8 < 1 → driver
        scores = BigFiveScores(
            openness=0.5,
            conscientiousness=0.8,
            extraversion=0.6,
            agreeableness=0.2,
            neuroticism=0.2,
        )
        assert compute_communication_style(scores) == "driver"

    def test_expressive(self) -> None:
        # assertive = E + (1-A) = 0.8+0.5 = 1.3 >= 1
        # responsive = A + E = 0.5+0.8 = 1.3 >= 1 → expressive
        scores = BigFiveScores(
            openness=0.8,
            conscientiousness=0.4,
            extraversion=0.8,
            agreeableness=0.5,
            neuroticism=0.5,
        )
        assert compute_communication_style(scores) == "expressive"


class TestArchetype:
    def test_investigator_match(self) -> None:
        scores = BigFiveScores(
            openness=0.8,
            conscientiousness=0.7,
            extraversion=0.3,
            agreeableness=0.4,
            neuroticism=0.4,
        )
        assert assign_archetype(scores) == "The Investigator"

    def test_diplomat_match(self) -> None:
        scores = BigFiveScores(
            openness=0.6,
            conscientiousness=0.5,
            extraversion=0.6,
            agreeableness=0.9,
            neuroticism=0.3,
        )
        assert assign_archetype(scores) == "The Diplomat"

    def test_always_returns_valid_archetype(self) -> None:
        scores = BigFiveScores(
            openness=0.5,
            conscientiousness=0.5,
            extraversion=0.5,
            agreeableness=0.5,
            neuroticism=0.5,
        )
        result = assign_archetype(scores)
        valid = {
            "The Investigator",
            "The Diplomat",
            "The Commander",
            "The Innovator",
            "The Guardian",
            "The Maverick",
        }
        assert result in valid


class TestDescription:
    def test_contains_archetype(self) -> None:
        scores = BigFiveScores(
            openness=0.8,
            conscientiousness=0.7,
            extraversion=0.3,
            agreeableness=0.4,
            neuroticism=0.4,
        )
        desc = generate_description(scores, "The Investigator")
        assert "The Investigator" in desc

    def test_non_empty(self) -> None:
        scores = BigFiveScores(
            openness=0.5,
            conscientiousness=0.5,
            extraversion=0.5,
            agreeableness=0.5,
            neuroticism=0.5,
        )
        desc = generate_description(scores, "The Guardian")
        assert len(desc) > 50


class TestComputePersonalityResult:
    def test_full_pipeline(self) -> None:
        answers = [ScenarioAnswer(question_id=i, option_index=1) for i in range(1, 11)]
        result = compute_personality_result(answers)
        assert result.scores is not None
        assert result.archetype in {
            "The Investigator",
            "The Diplomat",
            "The Commander",
            "The Innovator",
            "The Guardian",
            "The Maverick",
        }
        assert result.communication_style in {"analytical", "expressive", "driver", "amiable"}
        assert len(result.description) > 20


class TestCompatibility:
    def test_identical_agents(self) -> None:
        a = BigFiveScores(
            openness=0.5,
            conscientiousness=0.5,
            extraversion=0.5,
            agreeableness=0.5,
            neuroticism=0.5,
        )
        assert compute_compatibility(a, a) == 1.0

    def test_opposite_agents(self) -> None:
        a = BigFiveScores(
            openness=0.0,
            conscientiousness=0.0,
            extraversion=0.0,
            agreeableness=0.0,
            neuroticism=0.0,
        )
        b = BigFiveScores(
            openness=1.0,
            conscientiousness=1.0,
            extraversion=1.0,
            agreeableness=1.0,
            neuroticism=1.0,
        )
        compat = compute_compatibility(a, b)
        assert 0 <= compat < 0.5

    def test_range(self) -> None:
        a = BigFiveScores(
            openness=0.8,
            conscientiousness=0.3,
            extraversion=0.6,
            agreeableness=0.5,
            neuroticism=0.4,
        )
        b = BigFiveScores(
            openness=0.6,
            conscientiousness=0.5,
            extraversion=0.7,
            agreeableness=0.3,
            neuroticism=0.6,
        )
        compat = compute_compatibility(a, b)
        assert 0 <= compat <= 1


class TestSystemPrompt:
    def test_contains_agent_name(self) -> None:
        scores = BigFiveScores(
            openness=0.8,
            conscientiousness=0.7,
            extraversion=0.3,
            agreeableness=0.4,
            neuroticism=0.4,
        )
        prompt = generate_system_prompt(
            "Atlas",
            scores,
            "analytical",
            ["AI", "philosophy"],
            "OPEN",
            "Nova",
        )
        assert "Atlas" in prompt
        assert "Nova" in prompt
        assert "OPEN" in prompt
        assert "analytical" in prompt

    def test_includes_memories(self) -> None:
        scores = BigFiveScores(
            openness=0.5,
            conscientiousness=0.5,
            extraversion=0.5,
            agreeableness=0.5,
            neuroticism=0.5,
        )
        prompt = generate_system_prompt(
            "Test",
            scores,
            "analytical",
            ["AI"],
            "PROBE",
            "Other",
            memories=["Discussed AI safety yesterday"],
        )
        assert "AI safety" in prompt

    def test_includes_relationship(self) -> None:
        scores = BigFiveScores(
            openness=0.5,
            conscientiousness=0.5,
            extraversion=0.5,
            agreeableness=0.5,
            neuroticism=0.5,
        )
        prompt = generate_system_prompt(
            "Test",
            scores,
            "analytical",
            ["AI"],
            "CHALLENGE",
            "Peer",
            relationship={"conversation_count": 5, "strength": 0.7},
        )
        assert "5 prior conversations" in prompt
        assert "0.7" in prompt
