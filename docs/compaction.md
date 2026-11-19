# Context length and compaction

Every request sends the whole conversation: the system prompt, your messages, the model's answers and every tool result. The footer shows how much of the model's `contextWindow` from `models.json` that is. When it gets close, [compaction.py](../pi2/compaction.py) makes room, as Pi does:

<p align="center"><img alt="Compaction with a 32k model: before, the system prompt and twelve messages fill about 19k tokens, over the threshold of contextWindow minus reserveTokens, 16k. The older messages are summarized by compaction.summarize(); the newest, about keepRecentTokens, are kept word for word. After, the model sees the system prompt, the summary and the kept messages, about 11k tokens. The session file keeps every message." src="../assets/diagrams/compaction.svg" width="900"></p>

## How it works

1. **When.** Before each prompt and between turns, after the tool results are added, the session checks `context > contextWindow - reserveTokens`. The context is the model's last token count plus an estimate of the messages after it (four characters per token); before the model has counted, as at the start or right after a compaction, the system prompt and tool definitions are estimated too.
2. **What it keeps.** About `keepRecentTokens` of the newest messages, word for word. The cut never separates a tool call from its result.
3. **What it summarizes.** The older messages go to the model as plain text, with a request for a structured summary: goal, constraints, progress, key decisions, next steps, critical context. Files that `read`, `write` and `edit` touched are listed under it. A second compaction updates the first summary.
4. **What the model sees next.** The system prompt, the summary as a user message, then the kept messages. The session file keeps every message.

If the server still rejects a request as too long, the session compacts and retries once.

## What you see

When it compacts by itself, a dim line says why: "Context is filling up: summarizing older messages..." (or "Context too long" after a rejected request). Then a box shows what happened and the start of the summary:

```
 Compacted 5 messages, 19k → about 11k tokens

 ## Goal
 Fix the failing test in math.js.
 ## Constraints & Preferences
 - Keep the public API of math.js unchanged.
 ... (18 more lines)
```

The footer's percentage drops to match. The agent goes on with its task: compaction happens between turns, not instead of one.

## Looking inside: `/context`

The footer gives one number. `/context` shows where it comes from:

```
 Context about 15k of 33k tokens (46%) · compacts above 16k
 ██████████████████░░│░░░░░░░░░░░░░░░░░░░

 system prompt      310
 tools              640  (4)
 summary           1.3k  (1 message)
 your messages      120  (3 messages)
 answers           2.1k  (9 messages)
 tool results       10k  (8 messages)

 Parts are estimates (4 characters per token).
```

The bar is the window, and `│` marks where automatic compaction starts. The total is the same as the footer's: the model's last count plus an estimate of what came after it. The parts are estimates, so their sum is close to the total but not equal. Tool results are usually the largest part: that is what `/compact`, and exercise 05's subagent, make smaller.

## Compacting by hand: `/compact`

Type `/compact` in the editor to compact now, even below the threshold. Use it:

- before you switch to another task in the same session, so the old details stop taking room;
- after the agent has read large files it no longer needs;
- when the footer is close to the threshold and the next step will read more.

`/compact <focus>` adds your text to the request for the summary, so it keeps what matters to you: `/compact keep the exact error message of the failing test`. When the conversation is shorter than what is kept anyway, it says "Nothing to compact yet". ctrl+c stops a compaction and leaves the conversation as it was; so does a failed summary request, which shows its error.

A summary loses detail: exact file contents, long outputs, earlier reasoning. The model can read a file again, but it cannot recover what you said only once. Put that in the focus, or say it again after compacting.

## Settings

| Setting in `~/.pi/agent/settings.json` | Default | Meaning |
|---|---|---|
| `compaction.enabled` | `true` | Compact automatically |
| `compaction.reserveTokens` | 16384, at most half the window | Room left for the answer |
| `compaction.keepRecentTokens` | 20000, at most a quarter of the window | Newest messages kept word for word |

Pi uses 16384 and 20000 for every model. Lobotomized caps them for small windows, so that a 32k model compacts at 16k and keeps 8k: with Pi's numbers, the kept messages alone would be over the threshold and it would compact again on every turn.

The code is [pi2/compaction.py](../pi2/compaction.py), called from `AgentSession` in [pi2/session.py](../pi2/session.py). Pi's version, with split turns, branch summaries and extension hooks, is described in [its compaction reference](https://github.com/windx987/pi-2/blob/main/packages/coding-agent/docs/compaction.md).
