# Exercise 06: subagent

## Goal
- Build a tool that delegates a task to a second agent session.
- Ask the agent to divide the six incident reports between subagents and summarize them.

## Requirements
- Required: a non-empty `task`.
- Require `ctx.session`.
- Give the child the parent's runtime, model, cwd, and agent directory.
- Copy the parent's tools except `subagent`.
- Start with an empty context and run `child.prompt(task)`.
- Return the child's final text and a short usage note.
- Propagate errors and interrupts.

## Output

Return the child's final text, a blank line, then a short note:

```text
Found 3 files.

[subagent: 1 tool call, 3.0k input tokens]
```

Use `calls` for zero or two or more.

## Errors

Raise `ValueError` when `task` is empty or `ctx.session` is missing. Raise
`RuntimeError` with the child's message when its model fails. Re-raise
`KeyboardInterrupt` when the child is aborted.

## Hints
- Create a new `ExtensionAPI` for the child.
- Construct `AgentSession` with the parent's settings.
- Count `toolResult` messages for the usage note.

## Run
```bash
python3 -m pi2 --cwd playground/06-subagents \
  -e tools/01-read.py -e tools/06-subagent.py
```

## Check
```bash
python3 exercises/check.py 06
```
