# Lobotomized: pi/2 in Python (lean workshop)

A small coding agent in standard-library Python with a terminal UI. It has no built-in tools: you write `read`, `write`, `edit` and `bash` yourself. This branch is the workshop cut. The TypeScript Pi is not included.

## What is here

| Path | What it is |
|---|---|
| `python/pi2/` | The agent: CLI, UI, session, loop, provider, schema, extensions |
| `python/exercises/tools.py` | The file you edit: four tools plus a working `hello` |
| `python/playground/math.py` | A disposable file with one bug, for the tools to work on |
| `README.md` | Setup and exercises |
| `LICENSE` | MIT |

Everything else is intentionally absent.

## Requirements

- Python 3.10 or newer, no packages.
- [Ollama](https://ollama.com) for the model.
- Docker for exercise 04.

## Get the repository

```bash
git clone --depth 1 --single-branch -b lean https://github.com/windx987/pi-2.git
cd pi-2
```

The shallow clone keeps the download small.

## Model

Pull the model and give it a 32k context. Ollama's default of 4096 tokens is too small and cuts requests without an error:

```bash
ollama pull gemma4:12b
printf 'FROM gemma4:12b\nPARAMETER num_ctx 32768\n' > Modelfile
ollama create gemma4-workshop:12b -f Modelfile
```

Add the endpoint to `~/.pi/agent/models.json`, the same file Pi uses. For a shared Ollama server, replace `localhost` with its address:

```json
{
  "providers": {
    "ollama": {
      "baseUrl": "http://localhost:11434/v1",
      "api": "openai-completions",
      "apiKey": "ollama",
      "models": [
        { "id": "gemma4-workshop:12b", "name": "Gemma 4 12B (32k)", "contextWindow": 32768, "maxTokens": 8192 }
      ]
    }
  }
}
```

## Run

From the repository root:

```bash
cd python
python3 -m pi2 --model ollama/gemma4-workshop:12b -e exercises/tools.py
```

Ask "Greet Ada." The `hello` tool answers. The other four tools raise `NotImplementedError` until you implement them.

To run from a copy of the playground:

```bash
cp -R python/playground ~/pi-workshop
cd ~/pi-workshop
PYTHONPATH="$REPO/python" python3 -m pi2 --model ollama/gemma4-workshop:12b \
  -e "$REPO/python/exercises/tools.py"
```

`REPO` is the path to this clone. There is no install step; `PYTHONPATH` is enough.

| Key or command | Does |
|---|---|
| Enter | Send the message |
| ctrl+c | While the agent works: stop it. In the editor: clear it |
| ctrl+d | Exit |
| `/new`, `/quit`, `/help` | New session, exit, list commands |

## Exercises

Implement the four `execute_*` functions in `python/exercises/tools.py`, in this order. The comments above each function are the exercise.

### 01 Read

Let the agent read files. Resolve the path against `ctx.cwd`, read UTF-8 text, apply `offset` and `limit`, and raise an exception for a missing file. Ask:

- "What is in math.py?"
- "Show me lines 1 to 3 of math.py."

### 02 Write

Let the agent create files. Refuse paths outside `ctx.cwd`, create parent directories, write UTF-8, and return a short confirmation. Ask:

- "Create notes/todo.md with three workshop goals, then read it back."
- "Write a file to /tmp/outside.txt." It must be refused.

### 03 Edit

Let the agent change part of a file. Each `oldText` must occur exactly once in the original file; zero or two matches are errors, never guesses. Ask:

- "Fix the failing assertion in math.py."
- "In math.py, replace `return a - b` with `return a + b`."
- Copy that line twice and ask again: the edit must fail as ambiguous.

### 04 Bash

Let the agent run commands in a disposable container. Run the process, combine stdout and stderr, report a non-zero exit code as an error result, and honor `timeout`. Ask:

- "Run python3 math.py." It fails with exit code 1 until the edit is fixed.
- "Run sleep 30 with a 2 second timeout."

## Bash and Docker

Exercise 04 runs each command in a container. Pull the image once:

```bash
docker pull python:3.12-slim
```

`docker_args()` in `tools.py` sets `--rm`, no network, a 1 GB memory limit, 256 PIDs, only the working directory mounted at `/workspace`, and an init process so ctrl+c stops the command. Run from `~/pi-workshop`, because Docker and Colima share the home directory with containers.

Isolation checks:

| Check | Command | Expected |
|---|---|---|
| No network | `getent hosts example.com` | Fails to resolve |
| No host files outside the workspace | `ls /Users /home` | No host home directories |
| Memory limit | `python3 -c "a=[];\\nwhile True: a.append(bytearray(10**8))"` | Killed at about 1 GB |
| Timeout stops the container | `sleep 300` with `timeout: 2`, then `docker ps` | No container left |
| Cleanup after errors | a failing command, then `docker ps -a` | No leftover container |

SAFETY: `read`, `write` and `edit` run on the host. A symlink in the workspace that points outside it makes them reach the host. Resolve paths with `realpath` before the containment check if that matters for your setup.

## Extensions

An extension is any Python file loaded with `-e`. It has one function, `extension(pi)`, which pi2 calls at startup with an `ExtensionAPI`. An extension can register tools and listen to tool calls:

```python
def extension(pi):
    pi.register_tool(my_tool)          # offer a tool to the model

    def block(call, args):             # see every call before it runs
        return "reason" if dangerous else None

    pi.on("tool_call", block)
```

A tool is a `define_tool(...)` value: name, description, JSON Schema of its arguments, and `execute(params, ctx)`. Return a string; raise an exception for an error result. `ctx.cwd` is the working directory and `ctx.session` is the running session.

## How the agent works

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

## Notes

- Sessions are written to `~/.pi/agent/python-sessions/` but are not resumed.
- This branch has no tests and no packaging. Check the import path with `python3 -m pi2 --help`.
- One provider API is supported: `openai-completions`, which covers Ollama.

## License

MIT, as the original Pi.
