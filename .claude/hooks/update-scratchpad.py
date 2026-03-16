#!/usr/bin/env python3
"""Stop hook: Remind Claude to update the scratchpad after completing work."""
import json

result = {
    "continue": True,
    "additionalContext": "If you made significant changes, update .claude/scratchpad.md with: what you did, what's next, and any open questions."
}
print(json.dumps(result))
