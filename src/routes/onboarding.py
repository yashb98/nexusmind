"""Onboarding routes — scenarios and personality scoring."""

from fastapi import APIRouter

from src.models.onboarding import (
    AdaptiveOnboardingRequest,
    AdaptivePersonalityResult,
    OnboardingRequest,
    PersonalityResult,
    ScenarioQuestion,
)
from src.services.personality import (
    compute_adaptive_personality_result,
    compute_personality_result,
    get_scenarios,
    select_questions,
)

router = APIRouter(prefix="/api/v1/onboarding", tags=["onboarding"])


@router.get("/scenarios", response_model=list[ScenarioQuestion])
async def scenarios() -> list[ScenarioQuestion]:
    """Get 10 scenario-based personality questions."""
    return get_scenarios()


@router.post("/personality", response_model=PersonalityResult)
async def personality(req: OnboardingRequest) -> PersonalityResult:
    """Score personality from scenario answers."""
    return compute_personality_result(req.answers)


@router.get("/questions")
async def get_adaptive_questions(interests: str) -> list[dict]:
    """Get dynamically selected questions based on interests."""
    interest_list = [i.strip() for i in interests.split(",") if i.strip()]
    questions = select_questions(interest_list)
    return questions


@router.post("/personality/adaptive", response_model=AdaptivePersonalityResult)
async def adaptive_personality(
    req: AdaptiveOnboardingRequest,
) -> AdaptivePersonalityResult:
    """Score personality from adaptive questions with domain modifiers."""
    questions_as_dicts = [q.model_dump() for q in req.questions]
    result = compute_adaptive_personality_result(req.answers, questions_as_dicts)
    return AdaptivePersonalityResult(**result)
