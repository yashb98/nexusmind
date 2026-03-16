---
description: Fix a bug from an error trace or description. Claude's sweet spot.
---

1. Read the error trace or bug description below
2. Use a subagent to search the codebase for the relevant files:
   - Grep for the function/class names in the traceback
   - Read the files mentioned in the stack trace
   - Check related test files
3. Identify the root cause (not just the symptom)
4. Fix the root cause
5. Check: does this fix introduce any regressions? Look at callers of modified functions.
6. Run: `uv run pytest tests/unit/ -x --tb=short`
7. If the bug was in the frontend: also run `cd frontend && pnpm test --run`
8. If tests pass: explain what was wrong and why the fix works
9. If tests fail: iterate until they pass

Bug to fix: $ARGUMENTS
