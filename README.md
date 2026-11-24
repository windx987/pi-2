<p align="center">
  <img alt="pi/2 logo" src="./assets/logo.svg" width="128">
</p>
<p align="center">
  <a href="https://discord.com/invite/3cU7Bz4UPx"><img alt="Discord" src="https://img.shields.io/badge/discord-community-5865F2?style=flat-square&logo=discord&logoColor=white" /></a>
</p>

> This is the `python` branch: only the Python version of pi/2. The TypeScript edition, with the full Pi framework it is modelled on, is on [`main`](https://github.com/windx987/pi-2).

# pi/2 for Python

A small coding agent in Python, made to learn how an AI agent works. It starts with no tools: you write `read`, `write`, `bash` and `edit` yourself, in [exercises/](exercises/), and then watch the agent use them to read, run and fix code.

## Setup

Install steps are in [docs/setup.md](docs/setup.md). Model setup is in [docs/models.md](docs/models.md).

Clone the `python` branch:

```bash
git clone -b python https://github.com/windx987/pi-2.git ./pi-2
cd ./pi-2
```

pi2 reads `~/.pi/agent/models.json`, the same file Pi uses. To use a different folder, pass `--agent-dir DIR`; that folder holds `models.json` (and `settings.json`). The file lists providers, each with its models:

```json
{
  "providers": {
    "vllm": {
      "baseUrl": "http://localhost:8000/v1",
      "api": "openai-completions",
      "apiKey": "none",
      "models": [
        { "id": "Qwen/Qwen3-8B", "name": "Qwen3 8B", "contextWindow": 32768, "maxTokens": 8192 }
      ]
    }
  }
}
```

pi2 starts with the first model; `/model` lists them, `/model 2` switches, and `--model provider/id` starts with another. [docs/models.md](docs/models.md) has Ollama and vLLM setups, and [docs/setup.md](docs/setup.md) has the full install.

## Verify

```bash
python3 pi2.py --version
```

## Run

```bash
python3 pi2.py -e examples/hello.py
python3 pi2.py -e examples/hello.py --agent-dir .
```

In the playground, run from the clone:

```bash
python3 pi2.py --cwd playground -e exercises/01-read/read.py
```

## Options

| Option | Meaning |
|---|---|
| `--model ID` | Model as `provider/id` (or its number); default: the first in `models.json` |
| `--cwd DIR` | Directory the agent works in; default: the current directory |
| `--agent-dir DIR` | Directory holding `models.json` and `settings.json`; default: `~/.pi/agent` |
| `-e FILE` | Extension to load; repeatable |
| `--version` | Print the version |

## Exercises

| Exercise | Tool | Instructions |
|---|---|---|
| [01](exercises/01-read/read.py) | `read` | [README](exercises/01-read/README.md) |
| [02](exercises/02-write/write.py) | `write` | [README](exercises/02-write/README.md) |
| [03](exercises/03-bash/bash.py) | `bash` | [README](exercises/03-bash/README.md) |
| [04](exercises/04-edit/edit.py) | `edit` | [README](exercises/04-edit/README.md) |
| [05](exercises/05-subagent/subagent.py) | `subagent` | [README](exercises/05-subagent/README.md) |

Run each from the clone; `--cwd playground` keeps the agent's work there:

```bash
python3 pi2.py --cwd playground -e exercises/01-read/read.py
```

Add the next file with another `-e`; type `/new` to start over. Reset between exercises with `git restore playground && git clean -fd playground`.

Check a tool without a model: `python3 exercises/check.py 01` shows PASS, FAIL or TODO for each step of exercise 01. `python3 exercises/check.py` checks all five.

## Extensions

An extension is any Python file you load with `-e`. It has one function, `extension(pi)`, which pi2 calls at startup with an `ExtensionAPI`. Everything the model can do comes from extensions: pi2 itself contains no tools. Start it without `-e` and the model cannot read, write or run anything.

Through `pi`, an extension can do two things:

| Call | Does |
|---|---|
| `pi.register_tool(tool)` | Offers a tool to the model. Its `execute(params, ctx)` runs when the model calls it |
| `pi.on("tool_call", handler)` | Sees every tool call before it runs. `handler(call, args)` returns a reason to block it, or `None` |

[examples/hello.py](examples/hello.py) is the smallest tool: it greets someone by name. Load it with `python3 pi2.py -e examples/hello.py` and ask "Greet Ada." This is all of it:

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

`define_tool` describes the tool to the model: its name, a description, and the JSON Schema of its arguments. pi2 checks the model's arguments against that schema before `execute` runs, so `params` always has the right shape. `ctx.cwd` is the directory the agent works in, and `ctx.session` is the running `AgentSession`. Return a string; raise an exception for an error result, whose message the model reads.

A listener extension:

```python
def on_tool_call(call, args):
    if call["name"] == "bash" and "rm -rf" in args["command"]:
        return "Dangerous command blocked"   # the tool does not run; the model reads this
    return None                              # let the call run


def extension(pi):
    pi.on("tool_call", on_tool_call)
```

<p align="center"><img alt="One example, step by step. Left: the code of examples/hello.py and part of examples/permission_gate.py, with lines highlighted by step. Step 1: def extension(pi) with pi.register_tool(hello) in hello.py, and pi.on('tool_call', on_tool_call) in permission_gate.py. Step 3: name, description and parameters of define_tool, which the model sees. Step 5: parameters, which pi2 checks the arguments against, and on_tool_call, which returns None for a call that is not bash. Step 6: def execute(params, ctx). Step 7: its return value. Right: 1, you start pi2 and both files load; 2, you type Greet Ada.; 3, pi2 offers hello to the model; 4, the model answers hello({'name': 'Ada'}); 5, the arguments match and the listener lets the call run; 6, execute returns 'Hello, Ada!'; 7, the result goes back to the model." src="./assets/diagrams/extension-example.svg" width="900"></p>

Load several with repeated `-e`; they work together. How the modules fit together is in [docs/architecture.md](docs/architecture.md).

## Playground

[playground/](playground/README.md) has four scenarios, from a failing test to thirty incident reports. Each one explains the tools, what to ask and what to look for.

## License

MIT, as the original Pi.
