"""Integration tests for teach-back service."""

import uuid
from unittest.mock import AsyncMock, patch

from src.services import teachback


class TestTeachback:
    async def test_start_session(self) -> None:
        with (
            patch("src.services.teachback.postgres") as mock_pg,
            patch("src.services.teachback.llm_service") as mock_llm,
        ):
            mock_pg.fetchrow = AsyncMock(return_value=None)
            mock_pg.execute = AsyncMock()
            mock_llm.generate = AsyncMock(return_value="What do you already know about AI?")

            result = await teachback.start_session(
                user_id=str(uuid.uuid4()),
                insight_id="test-insight",
                insight_content="AI improves healthcare",
                topic="AI in Healthcare",
            )
            assert "session_id" in result
            assert result["bloom_level"] == 1
            assert "tutor_message" in result

    async def test_process_response(self) -> None:
        session_row = {
            "id": uuid.uuid4(),
            "user_id": uuid.uuid4(),
            "insight_id": "test",
            "topic": "AI",
            "bloom_level_start": 1,
            "bloom_level_end": None,
            "turns": 1,
            "status": "active",
        }
        with (
            patch("src.services.teachback.postgres") as mock_pg,
            patch("src.services.teachback.llm_service") as mock_llm,
        ):
            mock_pg.fetchrow = AsyncMock(return_value=session_row)
            mock_pg.execute = AsyncMock()
            mock_llm.generate = AsyncMock(return_value="Interesting! Can you elaborate on how?")

            result = await teachback.process_response(str(uuid.uuid4()), "AI helps with diagnosis")
            assert "tutor_message" in result
            assert result["turn"] == 2

    async def test_complete_session_levels_up(self) -> None:
        session_row = {
            "id": uuid.uuid4(),
            "user_id": uuid.uuid4(),
            "insight_id": "test",
            "topic": "AI",
            "bloom_level_start": 1,
            "bloom_level_end": None,
            "turns": 4,
            "status": "active",
        }
        with patch("src.services.teachback.postgres") as mock_pg:
            mock_pg.fetchrow = AsyncMock(return_value=session_row)
            mock_pg.execute = AsyncMock()

            result = await teachback.complete_session(str(uuid.uuid4()))
            assert result["leveled_up"] is True
            assert result["bloom_level_end"] == 2

    async def test_complete_session_no_levelup_few_turns(self) -> None:
        session_row = {
            "id": uuid.uuid4(),
            "user_id": uuid.uuid4(),
            "insight_id": "test",
            "topic": "AI",
            "bloom_level_start": 1,
            "bloom_level_end": None,
            "turns": 1,
            "status": "active",
        }
        with patch("src.services.teachback.postgres") as mock_pg:
            mock_pg.fetchrow = AsyncMock(return_value=session_row)
            mock_pg.execute = AsyncMock()

            result = await teachback.complete_session(str(uuid.uuid4()))
            assert result["leveled_up"] is False
