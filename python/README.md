# pi/2 in Python

A small Python version of pi/2, the Pi Workshop Edition. It follows the same eight steps as the [big picture](../README.md#the-big-picture), one file per part, in about 800 lines of standard-library Python. Its terminal looks and behaves like Pi's: the logo header, the editor between two borders, thinking in dim italics, tool calls in colored boxes, and the footer with tokens and model.

Like pi/2 it has no built-in tools. You write `read`, `write`, `edit` and `bash` as extensions, in [exercises/](exercises/).

## Run it

Requires Python 3.10 or newer, no packages. It uses the same `~/.pi/agent/models.json` as Pi, so the Ollama setup from the [Getting started](../README.md#getting-started) section works unchanged.

```bash
cd python
python -m pi2 --model ollama/gemma4-workshop:12b -e examples/hello.py
```

Or install the `pi2` command once with `pip install -e python`, then run `pi2` in any directory.

| Key or command | Does |
|---|---|
| Enter | Send the message |
| ctrl+c | While the agent works: stop it. In the editor: clear it |
| ctrl+d | Exit |
| `/new`, `/quit`, `/help` | New session, exit, list commands |

Text you type while the agent works waits in the editor for the next message.

## The eight steps in the code

| Step | Pi (TypeScript) | pi2 (Python) |
|---|---|---|
| 1. Interactive mode | `modes/interactive/interactive-mode.ts` | [pi2/tui.py](pi2/tui.py) `InteractiveMode.run` |
| 2. AgentSession | `core/agent-session.ts` | [pi2/session.py](pi2/session.py) `AgentSession.prompt` |
| 3. Agent loop | `packages/agent/src/agent-loop.ts` | [pi2/agent_loop.py](pi2/agent_loop.py) `run` |
| 4. streamFn and ModelRuntime | `core/sdk.ts`, `core/model-runtime.ts` | [pi2/model_runtime.py](pi2/model_runtime.py) `stream_fn` |
| 5. Provider → LLM | `packages/ai/src/api/openai-completions.ts` | [pi2/ai.py](pi2/ai.py) `stream` |
| 6. Validate, then ask extensions | `validateToolArguments`, `beforeToolCall` | [pi2/schema.py](pi2/schema.py), `AgentSession.before_tool_call` |
| 7. Tool runs | your extension's `execute()` | your extension's `execute()`, called in `agent_loop.execute_tool_call` |
| 8. Result back, saved | `currentContext.messages.push`, `appendMessage` | `agent_loop.run`, `AgentSession.save` |

Read them in that order. [pi2/extensions.py](pi2/extensions.py) is how tools get in, and [pi2/cli.py](pi2/cli.py) starts everything.

## Write a tool

```python
from pi2 import ExtensionAPI, define_tool


def execute(params, ctx):
    return f"Hello, {params['name']}!"


hello = define_tool(
    name="hello",
    label="hello",
    description="Greet someone by name",
    parameters={"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]},
    execute=execute,
)


def extension(pi: ExtensionAPI):
    pi.register_tool(hello)
```

`execute(params, ctx)` gets the validated arguments, `ctx.cwd` (the directory the agent works in) and `ctx.session` (the running `AgentSession`). Return a string; raise an exception for an error result, whose message the model reads. `pi.on("tool_call", handler)` lets an extension block calls: `handler(call, args)` returns a reason to block, or `None`.

## Exercises

| Exercise | Tool | Instructions |
|---|---|---|
| [01-read](exercises/01-read/starter.py) | `read` | [README](../education/exercises/01-read/README.md) |
| [02-write](exercises/02-write/starter.py) | `write` | [README](../education/exercises/02-write/README.md) |
| [03-edit](exercises/03-edit/starter.py) | `edit` | [README](../education/exercises/03-edit/README.md) |
| [04-bash](exercises/04-bash/starter.py) | `bash` | [README](../education/exercises/04-bash/README.md) |
| [05-subagent](exercises/05-subagent/starter.py) | `subagent` | [README](exercises/05-subagent/README.md) (Python only) |

The READMEs for 01 to 04 are the TypeScript exercises'; the tasks are the same, and each starter's comments name the Python functions to use. Work in a copy of the playground, as in the [exercise setup](../education/exercises/README.md):

```bash
cp -R education/playground ~/pi-workshop && cd ~/pi-workshop
python -m pi2 -e "$REPO/python/exercises/01-read/starter.py"     # with PYTHONPATH="$REPO/python", or after pip install
```

## What Pi does that pi2 leaves out

pi2 keeps the path of one prompt and drops the rest: one provider API (`openai-completions`, which covers Ollama), no Markdown rendering, no session resume, no compaction, no skills or slash-command extensions, no parallel tool calls, no image input. Text is wrapped by the terminal width as it streams. Sessions are saved to `~/.pi/agent/python-sessions/` but not loaded again.

## Tests

```bash
cd python
python -m unittest discover tests
```

The tests need no model: a fake stream function drives the agent loop, and a local HTTP server streams a recorded answer to the provider.
