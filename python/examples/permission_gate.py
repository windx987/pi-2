# An extension that registers no tool, only a rule for other tools: it blocks dangerous bash commands.
#
# Load it with your tools:
#   python -m pi2 -e exercises/04-bash/starter.py -e examples/permission_gate.py
# Then ask: "Delete the node_modules folder with rm -rf."
#
# pi2 gives every "tool_call" listener each call after the arguments are validated and before the tool
# runs (step 6). A listener that returns a reason blocks the call: the tool never runs, and the model
# gets the reason as an error result, so it can choose another way. The listener sees calls of every
# tool, including the ones other extensions register.
#
# Pi's version: packages/coding-agent/examples/extensions/permission-gate.ts

import re

from pi2 import ExtensionAPI

# Commands that are hard to undo. The same patterns as Pi's example.
DANGEROUS = [r"\brm\s+(-rf?|--recursive)", r"\bsudo\b", r"\b(chmod|chown)\b.*777"]


def on_tool_call(call, args):
    """Return a reason to block the call, or None to let it run."""
    if call["name"] != "bash":
        return None
    for pattern in DANGEROUS:
        if re.search(pattern, args["command"], re.IGNORECASE):
            return f"Dangerous command blocked: {args['command']}. Ask the user to run it themselves."
    return None


def extension(pi: ExtensionAPI):
    pi.on("tool_call", on_tool_call)
