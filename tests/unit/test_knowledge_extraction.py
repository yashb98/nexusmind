"""Tests for knowledge extraction — parsing LLM responses."""

from src.services.knowledge import _parse_extraction


class TestParseExtraction:
    def test_valid_json(self) -> None:
        response = (
            '{"insights": [{"content": "test", "importance": 0.8}],'
            ' "entities": [], "relations": []}'
        )
        result = _parse_extraction(response)
        assert len(result["insights"]) == 1
        assert result["insights"][0]["content"] == "test"

    def test_json_with_markdown_fences(self) -> None:
        response = (
            '```json\n{"insights": [{"content": "test"}], "entities": [], "relations": []}\n```'
        )
        result = _parse_extraction(response)
        assert len(result["insights"]) == 1

    def test_json_embedded_in_text(self) -> None:
        response = (
            "Here is the result: "
            '{"insights": [], "entities": [{"name": "AI"}], "relations": []}'
            " Done!"
        )
        result = _parse_extraction(response)
        assert len(result["entities"]) == 1
        assert result["entities"][0]["name"] == "AI"

    def test_invalid_json_returns_empty(self) -> None:
        response = "This is not JSON at all"
        result = _parse_extraction(response)
        assert result["insights"] == []
        assert result["entities"] == []
        assert result["relations"] == []

    def test_empty_response(self) -> None:
        result = _parse_extraction("")
        assert result["insights"] == []

    def test_complex_extraction(self) -> None:
        response = """{
            "insights": [
                {
                    "content": "Carbon-aware scheduling reduces costs",
                    "importance": 0.9,
                    "bloom_relevance": 3
                }
            ],
            "entities": [
                {
                    "name": "carbon-aware scheduling",
                    "type": "technology",
                    "description": "Scheduling considering carbon"
                },
                {
                    "name": "energy costs",
                    "type": "concept",
                    "description": "Cost of energy consumption"
                }
            ],
            "relations": [
                {
                    "source": "carbon-aware scheduling",
                    "target": "energy costs",
                    "type": "CAUSES",
                    "confidence": 0.85
                }
            ]
        }"""
        result = _parse_extraction(response)
        assert len(result["insights"]) == 1
        assert len(result["entities"]) == 2
        assert len(result["relations"]) == 1
        assert result["relations"][0]["type"] == "CAUSES"
