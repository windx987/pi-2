# What is in `core/`

[`packages/coding-agent/src/core/`](../../packages/coding-agent/src/core/) is the Pi application without its terminal UI, which lives in `src/modes/`. The [big picture](../../README.md#the-big-picture) uses five of its parts: `agent-session.ts` (step 2), `sdk.ts` and `model-runtime.ts` (step 4), `extensions/` (step 6), `tools/` (step 7) and `session-manager.ts` (step 8). The rest keeps a long session running, loads your settings and keys, and adds features the workshop does not need.

## The request path

| File | What it does |
|---|---|
| `agent-session.ts` | The center: turns your text into messages, declares tools, runs the agent, fires extension events, retries, compacts |
| `agent-session-runtime.ts`, `agent-session-services.ts` | Build a session and the services it uses |
| `sdk.ts` | Creates a session from options; holds the `streamFn` that sends requests through `ModelRuntime` |
| `model-runtime.ts` | Picks the provider for a model, adds the API key, calls pi-ai |
| `session-manager.ts` | Appends every message to the session file in `~/.pi/agent/sessions/`, loads it again for `--resume` |
| `messages.ts` | Pi's own message types next to the LLM messages |
| `system-prompt.ts` | Builds the system prompt: tools, project context files, skills |
| `event-bus.ts` | Passes session events to the UI and to extensions |

## Context length

| File | What it does |
|---|---|
| `compaction/compaction.ts` | Decides when to compact, finds the cut point, asks the model for a summary |
| `compaction/branch-summarization.ts` | Summarizes the branch you leave when you move with `/tree` |
| `compaction/utils.ts` | Turns messages into summary input, tracks which files were read and changed |
| `usage-totals.ts` | Adds up tokens and cost |
| `cache-stats.ts`, `cache-warmer.ts` | Prompt-cache hits and keeping the cache warm |
| `footer-data-provider.ts` | The footer data, including how full the context window is |

See [Compaction](#compaction) below.

## Tools

| Path | What it does |
|---|---|
| `tools/read.ts`, `write.ts`, `edit.ts`, `bash.ts`, `grep.ts`, `find.ts`, `ls.ts`, `powershell.ts` | In pi/2, only the schemas and types of the built-in tools: their `execute()` was removed. See [tool-removal.md](tool-removal.md) |
| `tools/truncate.ts` | Cuts tool output at 2000 lines or 50 KB, so one result cannot fill the context |
| `tools/edit-diff.ts` | Matching and diffs for `edit` |
| `tools/output-accumulator.ts`, `file-mutation-queue.ts`, `path-utils.ts` | Collects streamed output, orders writes to the same file, resolves paths |
| `tools/renderers/`, `render-utils.ts` | Draw tool calls and results in the terminal |
| `bash-executor.ts`, `exec.ts` | Run shell commands for the session (`AgentSession.executeBash`) and for extensions |
| `nested-tool-calls.ts` | Tool calls a tool makes while it runs (`ctx.executeTool()`) |
| `output-guard.ts` | Keeps stray writes to stdout from breaking the terminal UI |

## Extensions, skills, commands

| Path | What it does |
|---|---|
| `extensions/types.ts` | The extension API: `registerTool`, `on("tool_call")` and every other event |
| `extensions/loader.ts`, `jiti-loader.ts`, `virtual-modules.ts` | Load `.ts` extensions without a build step |
| `extensions/runner.ts`, `wrapper.ts` | Call extension handlers and wrap their tools |
| `skills.ts`, `prompt-templates.ts`, `slash-commands.ts` | Skills, prompt templates, `/` commands |
| `mcp-servers.ts`, `radius.ts`, `radius-mcp.ts` | MCP servers |
| `package-manager.ts`, `pi-manifest.ts` | Install Pi packages |

## Models, keys, settings

| Path | What it does |
|---|---|
| `model-registry.ts`, `model-resolver.ts`, `model-config.ts`, `models-store.ts`, `virtual-models.ts` | The model list, including your `~/.pi/agent/models.json`, and resolving `--model` |
| `provider-composer.ts`, `provider-matching.ts`, `preferred-providers.ts`, `remote-catalog-provider.ts` | Choose and combine providers |
| `auth-storage.ts`, `auth-guidance.ts`, `runtime-credentials.ts`, `resolve-config-value.ts` | API keys and `/login` |
| `http-dispatcher.ts`, `client-identity.ts` | Network settings for provider requests, and the `User-Agent` Pi sends |
| `settings-manager.ts`, `settings-defaults.ts`, `settings-schema.ts` | `~/.pi/agent/settings.json` and `.pi/settings.json` in the project |
| `keybindings.ts`, `project-trust.ts`, `trust-manager.ts`, `resource-loader.ts` | Key bindings, trusting a project's files, loading them |

## Everything else

`export-html/` exports a session as a web page. `telemetry.ts`, `timings.ts`, `diagnostics.ts`, `crash-log.ts` and `bug-report*.ts` record what went wrong. `index.ts` exports all of this for use as a library.

## Compaction

Every request sends the whole conversation: system prompt, your messages, the model's answers and every tool result. A few large files fill a 32k context fast. When the next request would not fit, the provider rejects it, and some servers, such as Ollama with its default context, cut it silently instead.

`AgentSession` keeps the context below the model's `contextWindow` from `models.json`:

1. **When.** Compaction starts when `contextTokens > contextWindow - reserveTokens` ([`shouldCompact`](../../packages/coding-agent/src/core/compaction/compaction.ts)). The session checks before each prompt and between turns, after tool results are added.
2. **What it keeps.** Walking back from the newest message, it keeps about `keepRecentTokens` as they are, and never cuts between a tool call and its result.
3. **What it summarizes.** Everything older goes to the model with a request for a structured summary: goal, constraints, progress, key decisions, next steps, critical context, and the files read and changed. A previous summary is updated, not repeated.
4. **What the model sees next.** System prompt, the summary, then the kept messages. The session file keeps everything; only the request gets shorter.

| Setting in `settings.json` | Default | Meaning |
|---|---|---|
| `compaction.enabled` | `true` | Compact automatically |
| `compaction.reserveTokens` | `16384` | Room left for the answer; compaction starts above `contextWindow - reserveTokens` |
| `compaction.keepRecentTokens` | `20000` | Recent messages kept word for word |

With the workshop's Gemma model at `contextWindow: 32768`, compaction starts at about 16k tokens.

Two more cases:

- **Overflow recovery.** If the provider still rejects the request as too long, or an answer stops early with `stopReason: "length"`, the session compacts once and retries ([`isContextOverflow`](../../packages/ai/src/utils/overflow.ts)).
- **By hand.** `/compact` compacts now; `/compact focus on the failing test` tells the summary what to keep.

Extensions can replace the summary or start a compaction: see [`custom-compaction.ts`](../../packages/coding-agent/examples/extensions/custom-compaction.ts) and [`trigger-compact.ts`](../../packages/coding-agent/examples/extensions/trigger-compact.ts). The full reference is [docs/compaction.md](../../packages/coding-agent/docs/compaction.md).

The Python version on the `python` branch has none of this: it shows how full the context is, and a request that does not fit ends the run with an error.
