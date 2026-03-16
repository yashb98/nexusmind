---
description: Write comprehensive tests for a feature or file, then run them
---

1. Read the source file(s) for: $ARGUMENTS
2. Identify all public functions and their contracts
3. For each function, write tests covering:
   - Happy path (normal input → expected output)
   - Edge cases (empty input, None, boundary values)
   - Error cases (invalid input → proper exception)
   - Permission checks (unauthorized access → 403)
   - Tenant isolation (no cross-tenant data leakage)
4. Test file location: mirror source path
   `src/services/personality.py` → `tests/unit/test_personality.py`
   `src/routes/agents.py` → `tests/integration/test_agents.py`
5. Use pytest + pytest-asyncio for async tests
6. Mock external services (LLM, Neo4j, Qdrant) in unit tests
7. Use real DB connections in integration tests (with test database)
8. Run: `uv run pytest tests/ -x --tb=short -v`
9. All tests must pass. Fix any failures.
10. Report coverage for the tested module

Feature to test: $ARGUMENTS
