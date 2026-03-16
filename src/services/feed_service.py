"""Feed service — activity feed aggregation."""

import uuid

import structlog

from src.db import postgres

logger = structlog.get_logger(__name__)


async def get_feed(user_id: str, limit: int = 50, offset: int = 0) -> list[dict]:
    """Get paginated feed items for a user."""
    rows = await postgres.fetch(
        """SELECT * FROM feed_items
           WHERE user_id = $1
           ORDER BY created_at DESC
           LIMIT $2 OFFSET $3""",
        uuid.UUID(user_id),
        limit,
        offset,
    )
    return [_row_to_dict(r) for r in rows]


async def create_feed_item(
    user_id: str,
    item_type: str,
    title: str,
    description: str | None = None,
    **kwargs: str | None,
) -> None:
    """Insert a new feed item for a user."""
    await postgres.execute(
        """INSERT INTO feed_items (user_id, item_type, title, description,
                                   related_conversation_id, related_group_id,
                                   related_event_id)
           VALUES ($1, $2, $3, $4, $5, $6, $7)""",
        uuid.UUID(user_id),
        item_type,
        title,
        description,
        uuid.UUID(kwargs["conversation_id"]) if kwargs.get("conversation_id") else None,
        uuid.UUID(kwargs["group_id"]) if kwargs.get("group_id") else None,
        uuid.UUID(kwargs["event_id"]) if kwargs.get("event_id") else None,
    )
    logger.info("feed_item_created", user_id=user_id, item_type=item_type)


async def mark_read(item_id: str) -> None:
    """Mark a feed item as read."""
    await postgres.execute(
        "UPDATE feed_items SET read = true WHERE id = $1",
        uuid.UUID(item_id),
    )


async def get_unread_count(user_id: str) -> int:
    """Get the number of unread feed items for a user."""
    count = await postgres.fetchval(
        "SELECT COUNT(*) FROM feed_items WHERE user_id = $1 AND read = false",
        uuid.UUID(user_id),
    )
    return count or 0


def _row_to_dict(row) -> dict:
    """Convert a database row to a serializable dict."""
    return {
        "id": str(row["id"]),
        "item_type": row["item_type"],
        "title": row["title"],
        "description": row.get("description"),
        "related_conversation_id": str(row["related_conversation_id"]) if row.get("related_conversation_id") else None,
        "related_group_id": str(row["related_group_id"]) if row.get("related_group_id") else None,
        "related_event_id": str(row["related_event_id"]) if row.get("related_event_id") else None,
        "read": row.get("read", False),
        "created_at": row["created_at"].isoformat(),
    }
