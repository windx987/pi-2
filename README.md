# pi/2 Python Workshop

## What is this repo

This repository is a lean fork of pi/2, the Pi Workshop Edition, used for educational workshops. It is a small coding agent written in standard-library Python with a terminal UI. It has no built-in tools: they live in `python/exercises/tools.py`. `hello` and `bash` work; `read`, `write` and `edit` are the exercises. The TypeScript version of Pi is not included.

| Path | What it is |
|---|---|
| `python/pi2/` | The agent: CLI, UI, session, loop, provider, schema, extensions |
| `python/exercises/tools.py` | The tools file: `hello` and `bash` work; `read`, `write` and `edit` are the exercises |
| `python/playground/math.py` | A disposable file with one bug, for the tools to work on |

## Requirements

- Python 3.10 or newer, no packages.
- An OpenAI-compatible LLM endpoint in the form `https://XXX/v1`, plus an API key if your endpoint requires one.

## Get started

Clone the repository. The shallow clone keeps the download small:

```bash
git clone --depth 1 --single-branch -b lean https://github.com/windx987/pi-2.git
cd pi-2
```

Set the endpoint. The quickest way is environment variables:

```bash
export PI_BASE_URL="https://XXX/v1"
export PI_MODEL="XXX"
export PI_API_KEY="XXX"
```

`PI_API_KEY` can be empty if your endpoint does not need one. You can also pass these values as flags; see [How to use](#how-to-use). pi2 still reads `~/.pi/agent/models.json` if you prefer a file.

The endpoint must accept `POST /chat/completions`. The context window defaults to 32768; change it with `PI_CONTEXT_WINDOW` or `--context-window`.

Check that the agent imports:

```bash
cd python
python3 -m pi2 --help
```

## How to use

### Run

With the environment variables set:

```bash
cd python
python3 -m pi2 -e exercises/tools.py
```

Or in one command:

```bash
python3 -m pi2 --base-url https://XXX/v1 --model XXX --api-key XXX -e exercises/tools.py
```

Ask "Greet Ada." The `hello` tool answers. The `read`, `write` and `edit` tools raise `NotImplementedError` until participants implement them.

To run from a copy of the playground:

```bash
cp -R python/playground ~/pi-workshop
cd ~/pi-workshop
PYTHONPATH="$REPO/python" python3 -m pi2 -e "$REPO/python/exercises/tools.py"
```

`REPO` is the path to this clone. There is no install step; `PYTHONPATH` is enough.

| Key or command | Does |
|---|---|
| Enter | Send the message |
| ctrl+c | While the agent works: stop it. In the editor: clear it |
| ctrl+d | Exit |
| `/new`, `/quit`, `/help` | New session, exit, list commands |

### Extensions

An extension is any Python file loaded with `-e`. It has one function, `extension(pi)`, which pi2 calls at startup with an `ExtensionAPI`. An extension can register tools and listen to tool calls:

```python
def extension(pi):
    pi.register_tool(my_tool)          # offer a tool to the model

    def block(call, args):             # see every call before it runs
        return "reason" if dangerous else None

    pi.on("tool_call", block)
```

A tool is a `define_tool(...)` value: name, description, JSON Schema of its arguments, and `execute(params, ctx)`. Return a string; raise an exception for an error result. `ctx.cwd` is the working directory and `ctx.session` is the running session.

### Code map

| Step | File |
|---|---|
| 1. Interactive mode | `python/pi2/tui.py` `InteractiveMode.run` |
| 2. AgentSession | `python/pi2/session.py` `AgentSession.prompt` |
| 3. Agent loop | `python/pi2/agent_loop.py` `run` |
| 4. streamFn and ModelRuntime | `python/pi2/model_runtime.py` `stream_fn` |
| 5. Provider to LLM | `python/pi2/ai.py` `stream` |
| 6. Validate, then ask extensions | `python/pi2/schema.py`, `AgentSession.before_tool_call` |
| 7. Tool runs | your `execute_*` in `python/exercises/tools.py` |
| 8. Result back, saved | `python/pi2/agent_loop.py` `run`, `AgentSession.save` |

Read them in that order. `python/pi2/extensions.py` is how extensions get in, and `python/pi2/cli.py` starts everything.

### Notes

- Sessions are written to `~/.pi/agent/python-sessions/` but are not resumed.
- The `bash` tool runs commands directly on the host as your user. There is no sandbox; work in a copy of the playground.
- This branch has no tests and no packaging. Check the import path with `python3 -m pi2 --help`.
- One provider API is supported: `openai-completions`.

## Original Pi framework

This edition is based on [earendil-works/pi](https://github.com/earendil-works/pi) at commit `cead615b4`. The original tool implementations are in git history there: `git show cead615b4:packages/coding-agent/src/core/tools/read.ts`. What was removed and why: [education/architecture/tool-removal.md](education/architecture/tool-removal.md). For Pi itself, see [pi.dev](https://pi.dev) and the [Pi documentation](https://pi.dev/docs/latest).

## License

MIT, as the original Pi.