"""Onboarding routes — scenarios and personality scoring."""

from fastapi import APIRouter

from src.models.onboarding import OnboardingRequest, PersonalityResult, ScenarioQuestion
from src.services.personality import compute_personality_result, get_scenarios

router = APIRouter(prefix="/api/v1/onboarding", tags=["onboarding"])


@router.get("/scenarios", response_model=list[ScenarioQuestion])
async def scenarios() -> list[ScenarioQuestion]:
    """Get 10 scenario-based personality questions."""
    return get_scenarios()


@router.post("/personality", response_model=PersonalityResult)
async def personality(req: OnboardingRequest) -> PersonalityResult:
    """Score personality from scenario answers."""
    return compute_personality_result(req.answers)
