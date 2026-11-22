# Exercise 06: subagents

Build `subagent`, a tool that delegates a self-contained task to another agent session.

## Task

From the repository root:

```bash
python3 -m pi2 --cwd playground/06-subagents \
  -e tools/01-read.py -e tools/06-subagent.py
```

Ask the agent to divide the six incident reports between three subagents, have each summarize its
reports, and combine the results.

## Contract

- Require a non-empty `task`.
- Use `ctx.session` as the parent session.
- Give the child the parent's runtime, model, working directory, and agent directory.
- Register every parent tool except `subagent` itself.
- Start the child with an empty context by calling `child.prompt(task)`.
- Return the text blocks from the child's final answer and a short usage note.
- Propagate model errors and `KeyboardInterrupt`.

## Hints

Create a new `ExtensionAPI`, copy the parent's tools into it, then construct `AgentSession`. Count
`toolResult` messages for the note and read input tokens from `child.usage`.

## Check

```bash
python3 exercises/check.py 06
```

The reference implementation is [`tools/06-subagent.py`](../../tools/06-subagent.py).
