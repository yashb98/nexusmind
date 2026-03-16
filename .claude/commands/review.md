---
description: Deep code review of current changes before committing
---

Review all uncommitted changes (git diff):

1. Use a subagent to check for security vulnerabilities:
   - SQL injection (raw string queries instead of parameterized)
   - Missing tenant_id filters (multi-tenancy leak)
   - Missing permission checks before data access
   - Hardcoded secrets or API keys
   - Missing Langfuse tracing on LLM calls

2. Check code quality:
   - Are all functions under 50 lines?
   - Do all functions have type hints?
   - Are Pydantic models used (not raw dicts)?
   - Is async used consistently (no blocking calls in async functions)?
   - Does every route follow the route → service → db pattern?

3. Check test coverage:
   - Does every new function have at least one test?
   - Are edge cases covered (empty input, invalid data, permission denied)?
   - Run: `uv run pytest tests/ -x --tb=short`

4. Check conventions:
   - CLAUDE.md conventions followed?
   - structlog used (not print)?
   - No PII in log statements?

5. Generate a summary:
   - What changed and why
   - Files modified/created
   - Any concerns or TODOs
   - Suggested commit message
