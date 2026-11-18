# Exercise 05b: a permission gate. An extension that registers no tool, only a rule for other tools.
#
# Load it with your tools:
#   python -m pi2 -e exercises/01-read/starter.py ... -e exercises/04-bash/starter.py \
#     -e exercises/05-extensions/permission_gate.py
# Then ask: "Delete the node_modules folder with rm -rf."
#
# LEARN:
# Step 6 has two halves. pi2 first checks the arguments against the tool's schema, then gives every
# "tool_call" listener the call before the tool runs. A listener that returns a reason blocks the call:
# the tool never runs, and the model gets the reason as an error result, so it can choose another way.
# The listener sees calls of every tool, including the ones other extensions register.
#
# TRACE:
# pi2/session.py      AgentSession.before_tool_call()
# pi2/agent_loop.py   execute_tool_call()
# Pi's version: packages/coding-agent/examples/extensions/permission-gate.ts

import re

from pi2 import ExtensionAPI

# Commands that are hard to undo. The same patterns as Pi's example.
DANGEROUS = [r"\brm\s+(-rf?|--recursive)", r"\bsudo\b", r"\b(chmod|chown)\b.*777"]


def on_tool_call(call, args):
    # call["name"] is the tool's name; args are its arguments, already checked against its schema.
    #
    # EXERCISE 1: Let every call through except bash: return None.
    #
    # EXERCISE 2: For bash, test args["command"] against each pattern in DANGEROUS
    # (re.search(pattern, command, re.IGNORECASE)). When one matches, return a reason, such as
    # "Dangerous command blocked: rm -rf". Write it for the model, which reads it.
    #
    # EXERCISE 3: Protect files too. Block write and edit calls whose args["path"] points into .git or
    # names a .env file.
    #
    # CHALLENGE: Ask instead of blocking. pi2 hides typed keys while the agent works (tui.no_echo), so
    # input() would read your answer without showing it. Find a way to ask "Allow? [y/N]" visibly.
    return None


def extension(pi: ExtensionAPI):
    pi.on("tool_call", on_tool_call)
