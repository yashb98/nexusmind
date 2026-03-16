---
description: Research a topic or explore the codebase before making changes
---

Use subagents to investigate: $ARGUMENTS

1. Spawn a subagent to search the codebase:
   - Grep for related function names, class names, imports
   - Read all files that touch this area
   - Map the call chain: who calls what, what depends on what

2. Spawn a subagent to check documentation:
   - Read relevant skills in .claude/skills/
   - Read SPEC.md for product requirements
   - Read docs/ARCHITECTURE.md for system design
   - Read docs/DECISIONS.md for past architectural choices

3. Summarize findings:
   - Current state: what exists and how it works
   - Dependencies: what would be affected by changes
   - Gaps: what's missing or broken
   - Recommended approach: how to implement/fix this
   - Risks: what could go wrong

4. Update .claude/scratchpad.md with findings

Do NOT write any code. Only research and report.
