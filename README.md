<p align="center">
  <img alt="pi/2 logo" src="./assets/logo.svg" width="128">
</p>

# Pi Workshop Edition (pi/2)

Pi Workshop Edition is an educational version of the [Pi agent framework](https://github.com/earendil-works/pi). It keeps Pi's architecture, packages and terminal UI, and removes the built-in coding tools (`read`, `write`, `edit`, `bash`, ...). In the workshop you write those tools yourself, as Pi extensions, and learn how a real agent works by completing it.

Start this edition without extensions and ask it to read a file: it cannot. The model is offered no tools. After the exercises it reads, writes, edits and runs code with tools you built.

## What you'll learn

- How an LLM provider, the agent loop and the terminal UI fit together in a real agent.
- How a tool call travels: from the model's request, through validation and execution, back to the model.
- How to define, register and implement tools with Pi's extension API.
- How to make tools safe: validating input, refusing ambiguous edits, isolating commands.

## Architecture

```mermaid
flowchart TB
    user([User])
    subgraph coding["packages/coding-agent"]
        tui["Interactive mode<br/>modes/interactive"]
        session["AgentSession<br/>core/agent-session.ts"]
        runner["ExtensionRunner<br/>core/extensions/runner.ts"]
        registry["Tool registry and loadout<br/>defaultTools, --tools"]
        sessions["SessionManager<br/>transcript, resume, compaction"]
        runtime["ModelRuntime<br/>core/model-runtime.ts"]
    end
    ext["Your extensions<br/>education/exercises"]
    subgraph agent["packages/agent - pi-agent-core"]
        loop["Agent and agent loop<br/>agent.ts, agent-loop.ts"]
    end
    subgraph ai["packages/ai - pi-ai"]
        providers["Providers, streaming,<br/>validateToolArguments"]
    end
    tuilib["packages/tui<br/>rendering library"]
    llm[("LLM provider API")]

    user --> tui
    tui --> tuilib
    tui -- "prompt()" --> session
    session -- "events" --> tui
    ext -- "pi.registerTool()" --> runner
    runner -- "registered tools" --> registry
    session --> registry
    registry -- "active tools: agent.state.tools" --> loop
    session -- "agent.prompt()" --> loop
    loop -- "events" --> session
    session -- "appendMessage()" --> sessions
    loop -- "beforeToolCall / afterToolCall" --> session
    session -- "tool_call / tool_result events" --> runner
    loop -- "streamFn" --> runtime
    runtime --> providers
    providers --> llm
    loop -- "execute()" --> ext
```

`coding-agent` depends on `agent`, `ai` and `tui` (and on `mcp` and `codemode` for built-in extensions); `agent` depends on `ai`, whose `validateToolArguments` the loop uses. The loop does not choose a provider: `AgentSession`'s `streamFn` sends requests through `ModelRuntime`, which resolves auth and calls the pi-ai provider. Your extensions enter only through the extension API. See [education/architecture/](education/architecture/) for details.

## How a request becomes a tool call

```mermaid
sequenceDiagram
    actor User
    participant TUI as Interactive mode
    participant Session as AgentSession
    participant AgentLoop as Agent loop (pi-agent-core)
    participant Model as ModelRuntime and pi-ai
    participant LLM as LLM provider
    participant Tool as Your tool

    User->>TUI: Fix the failing test
    TUI->>Session: prompt(text)
    Note over Session: active tools are already in agent.state.tools
    Session->>AgentLoop: agent.prompt(messages)
    loop until the model answers without tool calls
        AgentLoop->>Model: streamFn(model, messages and tool definitions)
        Model->>LLM: provider request
        LLM-->>Model: streamed response
        Model-->>AgentLoop: assistant message with a tool call
        AgentLoop-->>Session: message events
        Session-->>TUI: events, rendered as they stream
        AgentLoop->>AgentLoop: validateToolArguments(tool, call)
        AgentLoop->>Session: beforeToolCall
        Note over Session: extensions get a tool_call event and may block the call
        AgentLoop->>Tool: execute(toolCallId, params, signal, onUpdate, ctx)
        Tool-->>AgentLoop: content, details, isError
        AgentLoop->>Session: afterToolCall
        Note over Session: extensions get a tool_result event
        AgentLoop-->>Session: tool execution and result events
        Session-->>TUI: events
        Note over AgentLoop: the tool result joins the messages for the next request
    end
    AgentLoop-->>Session: final assistant message
    Note over Session: SessionManager.appendMessage persists each message
    Session-->>TUI: events
    TUI-->>User: rendered answer
```

The model decides which tool to call. Pi runs the tool lifecycle. You implement what the tool does.

## Learning path

```mermaid
flowchart LR
    a["Understand Pi"] --> b["Agent loop"] --> c["Tool calling"]
    c --> r["01 Read"] --> w["02 Write"] --> e["03 Edit"] --> s["04 Bash"]
    s --> x["Your own extensions"]
```

## Getting started

Requires Node.js 22.19 or newer, and Docker for exercise 04.

```bash
git clone https://github.com/windx987/pi-2.git
cd pi-2
npm install --ignore-scripts
npm run build
./pi-test.sh                      # run Pi from source; /login connects a provider
```

## Building your first tool

A tool is a definition plus one function, registered by an extension:

```typescript
import { defineTool, type ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { Type } from "typebox";

const hello = defineTool({
	name: "hello",
	label: "hello",
	description: "Greet someone by name",
	parameters: Type.Object({ name: Type.String() }),
	async execute(_toolCallId, params) {
		return { content: [{ type: "text", text: `Hello, ${params.name}!` }], details: undefined };
	},
});

export default function (pi: ExtensionAPI) {
	pi.registerTool(hello);
}
```

Load it with `./pi-test.sh -e hello.ts` and ask Pi to greet you.

## Workshop exercises

| Exercise | Tool | You learn |
|---|---|---|
| [01-read](education/exercises/01-read/README.md) | `read` | Arguments, filesystem access, error results |
| [02-write](education/exercises/02-write/README.md) | `write` | Structured input, validation, filesystem writes |
| [03-edit](education/exercises/03-edit/README.md) | `edit` | Exact matching, uniqueness, diffs, safe changes |
| [04-bash](education/exercises/04-bash/README.md) | `bash` | Processes, exit codes, isolation in Docker |

Start with [education/exercises/README.md](education/exercises/README.md). The full roadmap is in [education/README.md](education/README.md).

## Project structure

| Path | Contents |
|---|---|
| [packages/ai](packages/ai) | Multi-provider LLM API, streaming, model catalog |
| [packages/agent](packages/agent) | Agent loop, state, tool calling |
| [packages/coding-agent](packages/coding-agent) | The `pi` application: sessions, extensions, skills, interactive mode |
| [packages/tui](packages/tui) | Terminal UI library |
| [packages/mcp](packages/mcp), [packages/codemode](packages/codemode) | MCP integration and sandboxed JavaScript tool, used by built-in extensions |
| [packages/durable](packages/durable), [packages/chord](packages/chord), [apps/](apps) | Advanced runtimes and apps, outside the workshop path |
| [education/](education) | Workshop material: architecture notes, exercises, playground |

## Development

```bash
npm run check   # lint, format, type check (including the exercises)
./test.sh       # tests without API keys
```

See [AGENTS.md](AGENTS.md) for project rules.

## Original Pi framework

This edition is based on [earendil-works/pi](https://github.com/earendil-works/pi) at commit `cead615b4`. The original tool implementations are in git history there: `git show cead615b4:packages/coding-agent/src/core/tools/read.ts`. What was removed and why: [education/architecture/tool-removal.md](education/architecture/tool-removal.md). For Pi itself, see [pi.dev](https://pi.dev) and the [Pi documentation](https://pi.dev/docs/latest).

## License

MIT, as the original Pi.
