<p align="center">
  <img alt="pi/2 logo" src="./assets/logo.svg" width="128">
</p>

# pi/2 Python Workshop

## What is this repo

This repository is a lean fork of pi/2, the Pi Workshop Edition, used for educational workshops. It is a small coding agent written in standard-library Python with a terminal UI. It has no built-in tools: every tool comes from an extension in `tools/`, one file per tool. The TypeScript version of Pi is not included.

| Path | What it is |
|---|---|
| `pi2/` | The agent: CLI, UI, session, loop, provider, schema, extensions |
| `tools/` | One extension file per tool: `math.py`, `lsdir.py`, `find.py`, `read.py`, `write.py`, `edit.py`, `bash.py` |
| `tools/math.py` | The arithmetic tool, registered as `evaluate_equation` |
| `tools/lsdir.py` | List a directory, defaulting to the working directory |
| `tools/find.py` | Find files recursively by glob, defaulting to the working directory |
| `playground/math.py` | A disposable file with one bug, for the tools to work on |

## Requirements

- Python 3.10 or newer, no packages.
- An OpenAI-compatible LLM endpoint in the form `https://XXX/v1`, plus an API key if your endpoint requires one.

## Get started

Clone the repository. The shallow clone keeps the download small:

```bash
git clone -b lean https://github.com/windx987/pi-2.git
cd pi-2
```

Configure `settings.json`:

```json
{
  "agentDir": "~/.pi/agent",
  "provider": {
    "baseUrl": "http://localhost:11434/v1",
    "apiKey": "ollama",
    "model": "llama3.1",
    "contextWindow": 16384,
    "maxTokens": 4096
  }
}
```

Replace `baseUrl`, `apiKey`, `model` and the limits with your endpoint's values. The provider API defaults to `openai-completions`; the endpoint must accept `POST /chat/completions`.

For private settings, copy the file and pass it with `--settings`:

```bash
cp settings.json settings.local.json
# edit settings.local.json
```

`settings.local.json` is ignored by git.

Check that the agent imports:

```bash
python3 -m pi2 --help
```

There is no install step when you run from the repository root.

## How to use

### Run

Load every tool in `tools/`:

```bash
python3 -m pi2 -e tools
```

Load one tool:

```bash
python3 -m pi2 -e tools/math.py
```

Use a private settings file:

```bash
python3 -m pi2 --settings settings.local.json -e tools
```

Ask "What is 2 + 3?" The `math.py` extension registers the `evaluate_equation` tool. The other files register `lsdir`, `find_files`, `read`, `write`, `edit` and `bash`.

To work in a copy of the playground, so the agent does not change this repository:

```bash
cp -R playground ~/pi-workshop
cd ~/pi-workshop
PYTHONPATH="$REPO" python3 -m pi2 -e "$REPO/tools"
```

`REPO` is the path to this clone:

```bash
REPO=/path/to/pi-2
```

`PYTHONPATH` lets Python find the `pi2/` package from outside the repository. `-e` points at the tools folder in the repository. When you run from the repository root, neither is needed; use `python3 -m pi2 -e tools`.

| Key or command | Does |
|---|---|
| Enter | Send the message; while the agent works, queue another message |
| ctrl+c | While the agent works: clear queued messages; if none are queued, stop it. In the editor: clear it |
| ctrl+d | Exit |
| `/new`, `/quit`, `/help` | New session, exit, list commands. `/quit` exits immediately, even while the agent works |

### Extensions

An extension is any Python file loaded with `-e`. It has one function, `extension(pi)`, which pi2 calls at startup with an `ExtensionAPI`. An extension can register tools and listen to tool calls:

```python
def extension(pi):
    pi.register_tool(my_tool)          # offer a tool to the model

    def block(call, args):             # see every call before it runs
        return "reason" if dangerous else None

    pi.on("tool_call", block)
```

`-e` accepts a file or a folder. A folder loads every top-level `.py` file in sorted order and skips names that start with `_`. Load several files or folders by repeating `-e`.

A tool is a `define_tool(...)` value: name, description, JSON Schema of its arguments, and `execute(params, ctx)`. Return a string; raise an exception for an error result. `ctx.cwd` is the working directory and `ctx.session` is the running session.

### Code map

| Step | File |
|---|---|
| 1. Interactive mode | `pi2/tui.py` `InteractiveMode.run` |
| 2. AgentSession | `pi2/session.py` `AgentSession.prompt` |
| 3. Agent loop | `pi2/agent_loop.py` `run` |
| 4. streamFn and ModelRuntime | `pi2/model_runtime.py` `stream_fn` |
| 5. Provider to LLM | `pi2/ai.py` `stream` |
| 6. Validate, then ask extensions | `pi2/schema.py`, `AgentSession.before_tool_call` |
| 7. Tool runs | `execute` in `tools/*.py` |
| 8. Result back, saved | `pi2/agent_loop.py` `run`, `AgentSession.save` |

Read them in that order. `pi2/extensions.py` is how extensions get in, and `pi2/cli.py` starts everything.

### Notes

- Sessions are written to `~/.pi/agent/python-sessions/` but are not resumed.
- The `bash` tool runs commands directly on the host as your user. There is no sandbox; work in a copy of the playground.
- This branch has no tests and no packaging. Check the import path with `python3 -m pi2 --help`.
- One provider API is supported: `openai-completions`.

## Original Pi framework

This edition is based on [earendil-works/pi](https://github.com/earendil-works/pi) at commit `cead615b4`. The original tool implementations are in git history there: `git show cead615b4:packages/coding-agent/src/core/tools/read.ts`. For Pi itself, see [pi.dev](https://pi.dev) and the [Pi documentation](https://pi.dev/docs/latest).

## License

MIT, as the original Pi.
