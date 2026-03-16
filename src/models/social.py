"""Social layer models — groups, events, feed."""

from datetime import datetime
from pydantic import BaseModel, Field


class GroupCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    group_type: str = "interest"
    max_members: int = 20
    is_public: bool = True

class GroupResponse(BaseModel):
    id: str
    name: str
    description: str | None
    group_type: str
    created_by: str
    max_members: int
    is_public: bool
    member_count: int = 0
    created_at: str

class GroupDetail(GroupResponse):
    members: list[dict] = []
    recent_conversations: list[dict] = []

class EventCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    event_type: str = "debate"
    group_id: str | None = None
    max_participants: int = 20
    starts_at: datetime
    ends_at: datetime
    rules: dict = {}

class EventResponse(BaseModel):
    id: str
    name: str
    description: str | None
    event_type: str
    created_by: str
    group_id: str | None
    status: str
    max_participants: int
    participant_count: int = 0
    starts_at: str
    ends_at: str
    created_at: str

class FeedItem(BaseModel):
    id: str
    item_type: str
    title: str
    description: str | None
    related_agent_ids: list[str] = []
    read: bool = False
    created_at: str
