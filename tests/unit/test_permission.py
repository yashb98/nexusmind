"""Tests for permission service — level checks, audit logging."""

import uuid
from unittest.mock import AsyncMock, patch

from src.services import permission as permission_service


def _uid() -> str:
    return str(uuid.uuid4())


class TestGetEffectiveLevel:
    async def test_uses_override_when_set(self) -> None:
        with patch("src.services.permission.postgres") as mock_pg:
            mock_pg.fetchval = AsyncMock(return_value=3)
            level = await permission_service.get_effective_level(_uid(), _uid())
            assert level == 3

    async def test_falls_back_to_default(self) -> None:
        with patch("src.services.permission.postgres") as mock_pg:
            mock_pg.fetchval = AsyncMock(side_effect=[None, 2])
            level = await permission_service.get_effective_level(_uid(), _uid())
            assert level == 2

    async def test_returns_zero_when_no_default(self) -> None:
        with patch("src.services.permission.postgres") as mock_pg:
            mock_pg.fetchval = AsyncMock(side_effect=[None, None])
            level = await permission_service.get_effective_level(_uid(), _uid())
            assert level == 0


class TestCheckAccess:
    async def test_allowed_when_level_sufficient(self) -> None:
        with patch("src.services.permission.postgres") as mock_pg:
            mock_pg.fetchval = AsyncMock(return_value=3)
            mock_pg.execute = AsyncMock()
            allowed = await permission_service.check_access(
                _uid(), _uid(), 2, "conversation", _uid()
            )
            assert allowed is True

    async def test_denied_when_level_insufficient(self) -> None:
        with patch("src.services.permission.postgres") as mock_pg:
            mock_pg.fetchval = AsyncMock(return_value=1)
            mock_pg.execute = AsyncMock()
            allowed = await permission_service.check_access(
                _uid(), _uid(), 3, "conversation", _uid()
            )
            assert allowed is False

    async def test_always_logs_audit(self) -> None:
        with patch("src.services.permission.postgres") as mock_pg:
            mock_pg.fetchval = AsyncMock(return_value=5)
            mock_pg.execute = AsyncMock()
            await permission_service.check_access(_uid(), _uid(), 1, "memory", _uid())
            assert mock_pg.execute.called


class TestSetPermission:
    async def test_calls_upsert(self) -> None:
        with patch("src.services.permission.postgres") as mock_pg:
            mock_pg.execute = AsyncMock()
            await permission_service.set_permission(_uid(), _uid(), 3, _uid())
            assert mock_pg.execute.called
