#!/usr/bin/env python3
"""PreToolUse hook: Block dangerous commands before Claude runs them."""
import json
import os
import sys

BLOCKED_PATTERNS = [
    "rm -rf /",
    "rm -rf ~",
    "rm -rf .",
    "DROP TABLE",
    "DROP DATABASE",
    "TRUNCATE",
    "sudo rm",
    "chmod 777",
    "> /dev/sda",
    "mkfs.",
    ":(){:|:&};:",
    "curl | sh",
    "curl | bash",
    "wget | sh",
    "pip install --break-system-packages" ,  # except in containers
    "DELETE FROM agents",  # protect production data
    "DELETE FROM users",
    "DELETE FROM tenants",
]

WARN_PATTERNS = [
    "docker system prune",
    "git push --force",
    "git reset --hard",
    "DROP INDEX",
    "ALTER TABLE.*DROP",
    "TRUNCATE",
]

def check_command():
    tool_input = os.environ.get("CLAUDE_TOOL_INPUT", "{}")
    try:
        data = json.loads(tool_input)
        command = data.get("command", "")
    except json.JSONDecodeError:
        command = tool_input

    for pattern in BLOCKED_PATTERNS:
        if pattern.lower() in command.lower():
            result = {
                "continue": False,
                "message": f"BLOCKED: Command contains dangerous pattern '{pattern}'. This command will not be executed."
            }
            print(json.dumps(result))
            sys.exit(2)

    for pattern in WARN_PATTERNS:
        if pattern.lower() in command.lower():
            result = {
                "continue": True,
                "message": f"WARNING: Command contains potentially dangerous pattern '{pattern}'. Proceeding with caution."
            }
            print(json.dumps(result))
            return

    result = {"continue": True}
    print(json.dumps(result))

if __name__ == "__main__":
    check_command()
