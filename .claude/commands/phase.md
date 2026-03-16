---
description: Execute a specific migration step from MIGRATION.md with full context loading and verification
---

1. Read MIGRATION.md to find step $ARGUMENTS
2. Read the context file referenced in that step (context/*.md)
3. Read all relevant skill files from .claude/skills/
4. Read .claude/scratchpad.md for current project state

Before implementing:
5. Check: what exists already? Don't rebuild working code.
6. Plan the exact changes (file paths, what's added vs modified)
7. Present the plan — wait for confirmation if changes are large

During implementation:
8. NEVER delete existing working code — only ADD, MODIFY, or EXTEND
9. NEVER rename existing API endpoints — only ADD new ones
10. NEVER change database column types — only ADD columns
11. Follow patterns from the relevant skills

After implementation:
12. Run existing tests: `uv run pytest tests/ -x --tb=short`
13. Run new tests for this step
14. If any EXISTING test broke: fix it before proceeding
15. Update .claude/scratchpad.md with what was done
16. Suggest: `git add . && git commit -m "feat: migration step $ARGUMENTS complete"`

Migration step to execute: $ARGUMENTS
