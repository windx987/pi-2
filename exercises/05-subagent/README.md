# Exercise 05: subagent (Python only)

A subagent is a tool whose `execute()` runs a whole second agent. The parent model calls `subagent` with a task. A new `AgentSession` with an empty conversation does the work with the same tools, and only its final answer comes back as the tool result.

## What you learn

- That a tool can run a whole agent: its `execute()` starts a second `AgentSession` with the same model and tools.
- Why the context grows: everything the agent reads stays in its messages and is sent with every later request.
- How a tool reaches the running session through `ctx.session`, as every extension can.

## How it works

Like the tools in 01 to 04, this is an extension that registers one tool. What is new is what the tool does. Say you ask "what does each file in this project do?":

- **Without a subagent:** the parent reads 10 files. Their full text stays in its context for the rest of the conversation.
- **With a subagent:** the subagent reads the 10 files in its own context and answers in one paragraph. The parent's context grows by that paragraph only.

1. The parent model calls `subagent({"task": "..."})`. For the parent this is step 7 of [the eight steps](../../README.md#the-eight-steps-in-the-code), like any tool.
2. `execute()` gives a new `ExtensionAPI` the parent's tools, without `subagent`, and starts an `AgentSession` with the parent's runtime and model and no messages.
3. `child.prompt(task)` runs steps 2 to 8 again, in the child's own context. Nothing listens to the child's events, so the terminal shows only the parent's `subagent` box while it works.
4. The text of the child's last message becomes the tool result. The parent sees one result, not the files behind it.

The subagent does not see the conversation, so the task it gets must be complete. Compaction ([`/compact`](../../docs/compaction.md)) is the other way to keep the context small: it summarizes after the fact, and the summary loses detail. A subagent keeps the files out of the parent's context from the start.

## Steps

Follow the comments in [subagent.py](subagent.py):

1. Give the subagent the parent's tools, except `subagent` itself.
2. Create the child `AgentSession` and call `prompt(task)`.
3. Turn a failed or aborted subagent into an error, or into ctrl+c for the parent.
4. Return the text of its last message, with a note on what it cost.

## Check your tool

Before you try it with the model, check it without one:

```bash
python3 exercises/check.py 05
```

Each step of the list above has checks that call your `execute()` directly. A check shows PASS, FAIL with what went wrong, or TODO while `execute()` still raises `NotImplementedError`. When all checks pass, the tool does what the steps ask. A fake model plays the subagent, so no model is needed. Whether the model uses the tool well is what the next section shows.

## Try it

From your playground copy, load your read tool and the subagent (your read tool must work first: the subagent has only the tools you load):

```bash
cd ~/pi-workshop
"$REPO/pi2.sh" -e "$REPO/exercises/01-read/read.py" -e "$REPO/exercises/05-subagent/subagent.py"
```

The playground's [incidents/](../../playground/incidents/) has 30 incident reports, about 25k tokens: past the 16k where a 32k model compacts, while each subagent's 10 reports, about 9k, fit. Ask:

"The reports in incidents/ are INC-2601.md to INC-2630.md. Use three subagents: the first reads INC-2601.md to INC-2610.md, the second INC-2611.md to INC-2620.md, the third INC-2621.md to INC-2630.md. Each one reads the Root cause section of every report, not the logs, and returns one line per report: the incident number, the date, the root cause, and yes if the root cause says the database failed, no if something else did. Then list the yes lines, numbered."

Name the files and what to return: neither tool can list a folder, and a subagent sees only its task, not your conversation. Without the names the model guesses, such as `incidents/1.txt`. Ask for a line per report, not only the matches: a report the subagent skipped or misjudged then shows up as a wrong "no" you can check, instead of silently missing. Ask for numbered lines rather than a count: a model writes 1, 2, 3 reliably, but a count it states is a guess and can be off by one.

Then type `/new` and ask the same without subagents. See [scenario 2 of the playground](../../playground/README.md#2-thirty-incident-reports) for what to look for.

<p align="center"><img alt="Try it for subagent: the ask gives three subagent calls, each grey while it reads 10 reports and then green with 10 yes or no lines and the cost note, then the yes lines numbered; /context shows only the three lists in the parent's context. Hint: give each subagent a complete task, and expect a few minutes." src="../../assets/diagrams/exercise-05-try.svg" width="900"></p>

## Expected result

- Three `subagent` boxes, each grey while its subagent works, then green with its list and your note, such as `[subagent: 10 tool calls, 48.2k input tokens]`.
- The parent answers from those results, without calling `read` itself.
- The footer's percentage grows by about the size of the three lists. Without subagents, the context fills up and the session compacts: `/context` shows the tool results the parent kept.
- ctrl+c while the subagent works stops the subagent and the parent.

## Where to look

| File | What to look at |
|---|---|
| [pi2/session.py](../../pi2/session.py) | `AgentSession.__init__` and `prompt`: what the subagent runs |
| [pi2/extensions.py](../../pi2/extensions.py) | `ToolContext`: `ctx.session`, the session running the tool |
| [pi2/agent_loop.py](../../pi2/agent_loop.py) | `execute_tool_call`: ctrl+c inside a tool ends the parent's loop too |

## In Pi

Pi has no built-in subagent either. Its example extension, [examples/extensions/subagent/](https://github.com/windx987/pi-2/tree/main/packages/coding-agent/examples/extensions/subagent), starts a separate `pi --mode json -p --no-session` process per task and reads its event stream. That gives it parallel tasks, streamed progress and roles defined in Markdown files. This exercise keeps the idea and runs the second agent in the same process.
