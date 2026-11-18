# pi/2 Python Workshop

## What is this repo

This repository is a lean fork of pi/2, the Pi Workshop Edition, used for educational workshops. It is a small coding agent written in standard-library Python with a terminal UI. It has no built-in tools: they live in `python/exercises/tools.py`. `hello` and `bash` work; `read`, `write` and `edit` are the exercises. The TypeScript version of Pi is not included.

| Path | What it is |
|---|---|
| `settings.json` | The one config file: endpoint, model, key and agent directory |
| `python/pi2/` | The agent: CLI, UI, session, loop, provider, schema, extensions |
| `python/exercises/tools.py` | The tools file: `hello` and `bash` work; `read`, `write` and `edit` are the exercises |
| `python/playground/math.py` | A disposable file with one bug, for the tools to work on |

## Requirements

- Python 3.10 or newer, no packages.
- An OpenAI-compatible LLM endpoint in the form `https://XXX/v1`, plus an API key if your endpoint requires one.

## Get started

Clone the repository:

```bash
git clone -b lean https://github.com/windx987/pi-2.git
cd pi-2
```

Edit `settings.json` in the repository root. Replace the endpoint, model id and key with yours:

```json
{
  "agentDir": "~/.pi/agent",
  "provider": {
    "baseUrl": "http://localhost:8000/v1",
    "api": "openai-completions",
    "apiKey": "local",
    "model": "local-model",
    "name": "Local model",
    "contextWindow": 32768,
    "maxTokens": 8192
  }
}
```

- `baseUrl` must accept `POST /chat/completions`.
- `model` is the model id sent to the endpoint.
- `apiKey` can be `local` for a local server that ignores it. Use `""` if the server does not want an `Authorization` header.
- `agentDir` is where sessions are written. Relative paths are resolved from the directory containing `settings.json`.
- `contextWindow` defaults to 32768. `maxTokens` is optional.

The repository copy uses a dummy local key. For a real key, keep it out of git:

```bash
cp settings.json settings.local.json
# edit settings.local.json
```

`settings.local.json` is ignored by git.

Check that the agent imports:

```bash
cd python
python3 -m pi2 --help
```

## How to use

### Run

From `python/`:

```bash
python3 -m pi2 -e exercises/tools.py
```

The default settings file is `settings.json` in the repository root, independent of the current directory.

Use a private settings file:

```bash
cd python
python3 -m pi2 --settings ../settings.local.json -e exercises/tools.py
```

`--settings` accepts a path relative to the current directory or an absolute path.

Ask "Greet Ada." The `hello` tool answers. The `read`, `write` and `edit` tools raise `NotImplementedError` until participants implement them.

To run from a copy of the playground:

```bash
cp -R python/playground ~/pi-workshop
cd ~/pi-workshop
PYTHONPATH="$REPO/python" python3 -m pi2 -e "$REPO/python/exercises/tools.py"
```

`REPO` is the path to this clone. Add `--settings "$REPO/settings.local.json"` to use a private settings file.

| Key or command | Does |
|---|---|
| Enter | Send the message |
| ctrl+c | While the agent works: stop it. In the editor: clear it |
| ctrl+d | Exit |
| `/new`, `/quit`, `/help` | New session, exit, list commands |

### Extensions

An extension is any Python file loaded with `-e`. It has one function, `extension(pi)`, which pi2 calls at startup with an `ExtensionAPI`. `-e` is repeatable, and an extension can register tools and listen to tool calls:

```python
def extension(pi):
    pi.register_tool(my_tool)          # offer a tool to the model

    def block(call, args):             # see every call before it runs
        return "reason" if dangerous else None

    pi.on("tool_call", block)
```

A tool is a `define_tool(...)` value: name, description, JSON Schema of its arguments, and `execute(params, ctx)`. Return a string; raise an exception for an error result. `ctx.cwd` is the working directory and `ctx.session` is the running session.

Without `-e`, no tools are loaded: the model cannot read, write or run anything. `python/exercises/tools.py` registers `hello`, `read`, `write`, `edit` and `bash`.

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

- Sessions are written to `<agentDir>/python-sessions/`; the default is `~/.pi/agent/python-sessions/`. They are not resumed.
- The `bash` tool runs commands directly on the host as your user. There is no sandbox; work in a copy of the playground.
- This branch has no tests and no packaging. Check the import path with `python3 -m pi2 --help`.
- One provider and one model are configured at a time. Edit `settings.json`, or pass a different `--settings` file.
- One provider API is supported: `openai-completions`.

MIT, as the original Pi.
