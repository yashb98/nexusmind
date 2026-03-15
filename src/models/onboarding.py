"""Onboarding request/response models."""

from pydantic import BaseModel, Field


class ScenarioOption(BaseModel):
    """A single option in a scenario question."""

    text: str
    scores: dict[str, float]


class ScenarioQuestion(BaseModel):
    """A scenario-based personality question."""

    id: int
    scenario: str
    options: list[ScenarioOption]


class ScenarioAnswer(BaseModel):
    """User's answer to a scenario question."""

    question_id: int
    option_index: int = Field(ge=0, le=3)


class BigFiveScores(BaseModel):
    """Big Five personality scores (0-1 each)."""

    openness: float = Field(ge=0, le=1)
    conscientiousness: float = Field(ge=0, le=1)
    extraversion: float = Field(ge=0, le=1)
    agreeableness: float = Field(ge=0, le=1)
    neuroticism: float = Field(ge=0, le=1)


class PersonalityResult(BaseModel):
    """Result of personality scoring."""

    scores: BigFiveScores
    archetype: str
    communication_style: str
    description: str


class OnboardingRequest(BaseModel):
    """Onboarding request with scenario answers."""

    answers: list[ScenarioAnswer] = Field(min_length=10, max_length=10)
