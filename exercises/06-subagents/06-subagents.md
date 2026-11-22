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
