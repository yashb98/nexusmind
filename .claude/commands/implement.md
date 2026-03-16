---
description: Implement a feature following NexusMind engineering standards with full verification
---

Before writing any code:
1. Read CLAUDE.md for conventions and constraints
2. Read the relevant skill files in .claude/skills/ for domain patterns
3. If a context file exists in context/ for this feature, read it
4. Use a subagent to scan the codebase for related patterns and existing code
5. Create a numbered plan with exact file paths and what changes in each

During implementation:
6. Follow the route → service → db pattern (never put logic in routes)
7. Type hints on every function, Pydantic models for all data
8. Every DB query must filter by tenant_id
9. Every LLM call must be wrapped in Langfuse trace
10. Fire-and-forget for non-blocking operations (asyncio.create_task)
11. Parallel I/O with asyncio.gather for independent operations

After implementation:
12. Run: `uv run ruff check src/ --fix && uv run ruff format src/`
13. Run: `uv run pytest tests/unit/ -x --tb=short`
14. Run: `uv run pytest tests/integration/ -x --tb=short` (if integration tests exist for this feature)
15. Self-review: What are the failure modes? What would a senior reviewer flag?
16. Fix any issues found in self-review
17. All tests must pass before considering this done

Feature to implement: $ARGUMENTS
