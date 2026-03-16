"""Agent CRUD routes (tenant-scoped)."""

from fastapi import APIRouter, Depends, HTTPException, status

from src.models.agent import AgentCreate, AgentResponse, AgentUpdate
from src.services import agent_service
from src.utils.auth import get_current_user

router = APIRouter(prefix="/api/v1/agents", tags=["agents"])


@router.post("", response_model=AgentResponse, status_code=201)
async def create_agent(
    req: AgentCreate, current_user: dict = Depends(get_current_user)
) -> AgentResponse:
    """Create a new agent."""
    return await agent_service.create_agent(req, current_user["user_id"], current_user["tenant_id"])


@router.get("", response_model=list[AgentResponse])
async def list_agents(
    current_user: dict = Depends(get_current_user),
) -> list[AgentResponse]:
    """List all agents in tenant."""
    return await agent_service.list_agents(current_user["tenant_id"])


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: str, current_user: dict = Depends(get_current_user)) -> AgentResponse:
    """Get agent by ID."""
    agent = await agent_service.get_agent(agent_id, current_user["tenant_id"])
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    return agent


@router.patch("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: str,
    req: AgentUpdate,
    current_user: dict = Depends(get_current_user),
) -> AgentResponse:
    """Update agent fields."""
    agent = await agent_service.update_agent(agent_id, current_user["tenant_id"], req)
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    return agent


@router.delete("/{agent_id}", status_code=204)
async def delete_agent(agent_id: str, current_user: dict = Depends(get_current_user)) -> None:
    """Delete an agent."""
    deleted = await agent_service.delete_agent(agent_id, current_user["tenant_id"])
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")


@router.post("/{agent_id}/retake-quiz")
async def retake_quiz(
    agent_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Clear personality scores to allow re-onboarding."""
    await agent_service.update_agent(agent_id, current_user["tenant_id"], {
        "openness": 0.5, "conscientiousness": 0.5, "extraversion": 0.5,
        "agreeableness": 0.5, "neuroticism": 0.5,
        "personality_confidence": 0.0, "questions_answered": 0,
        "domain_modifiers": {},
    })
    return {"status": "reset", "redirect": "/onboarding?step=2"}


@router.get("/{agent_id}/learning-progress")
async def get_learning_progress(
    agent_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get learning progress for the agent's owner."""
    # For now return a placeholder since learner_knowledge table may not exist yet
    return {
        "topics": [],
        "total_sessions": 0,
        "average_bloom": 0,
    }
