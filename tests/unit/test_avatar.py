"""Tests for avatar service — presets."""

from src.services.avatar import get_presets


class TestAvatarPresets:
    def test_returns_6_presets(self) -> None:
        presets = get_presets()
        assert len(presets) == 6

    def test_presets_have_required_fields(self) -> None:
        for preset in get_presets():
            assert "id" in preset
            assert "name" in preset
            assert "url" in preset
