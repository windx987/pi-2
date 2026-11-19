# Exercise 05: subagent (Python only)

A subagent is a tool whose `execute()` runs a whole second agent. The parent model calls `subagent` with a task. A new `AgentSession` with an empty conversation does the work with the same tools, and only its final answer comes back as the tool result.

Like the tools in 01 to 04, it is an extension that registers one tool. What is new is what that tool does: it uses `ctx.session`, the running session, to reach the model, the runtime and the other tools.

## Why

Everything the agent reads stays in its messages and is sent with every later request. Say you ask "what does each file in this project do?":

- **Without a subagent:** the parent reads 10 files. Their full text stays in its context for the rest of the conversation.
- **With a subagent:** the subagent reads the 10 files in its own context and answers in one paragraph. The parent's context grows by that paragraph only.

Compaction ([`/compact`](../../README.md#context-length-and-compaction)) is the other way to keep the context small: it summarizes after the fact, and the summary loses detail. A subagent keeps the files out of the parent's context from the start.

The subagent does not see the conversation, so the task it gets must be complete.

## Steps

Follow the comments in [starter.py](starter.py):

1. Give the subagent the parent's tools, except `subagent` itself.
2. Create the child `AgentSession` and call `prompt(task)`.
3. Return the text of its last message, with a note on what it cost.
4. Turn a failed or aborted subagent into an error, or into ctrl+c for the parent.

## Check your tool

Before you try it with the model, check it without one:

```bash
python3 exercises/check.py 05
```

Each step of the list above has checks that call your `execute()` directly. A check shows PASS, FAIL with what went wrong, or TODO while `execute()` still raises `NotImplementedError`. When all checks pass, the tool does what the steps ask. A fake model plays the subagent, so no model is needed. Whether the model uses the tool well is what the next section shows.

## Try it

```bash
./pi2.sh -e exercises/01-read/starter.py -e exercises/05-subagent/starter.py
```

Ask: "Use a subagent to find out what each file in this directory does." Your read tool must work first: the subagent has only the tools you load. Compare the footer's context percentage with and without the subagent.

## In Pi

Pi has no built-in subagent either. Its example extension, [examples/extensions/subagent/](https://github.com/windx987/pi-2/tree/main/packages/coding-agent/examples/extensions/subagent), starts a separate `pi --mode json -p --no-session` process per task and reads its event stream. That gives it parallel tasks, streamed progress and roles defined in Markdown files. This exercise keeps the idea and runs the second agent in the same process.
