<p align="center">
  <img alt="pi/2 logo" src="./assets/logo.svg" width="128">
</p>
<p align="center">
  <a href="https://discord.com/invite/3cU7Bz4UPx"><img alt="Discord" src="https://img.shields.io/badge/discord-community-5865F2?style=flat-square&logo=discord&logoColor=white" /></a>
  <a href="https://www.npmjs.com/package/@earendil-works/pi-coding-agent"><img alt="npm" src="https://img.shields.io/npm/v/@earendil-works/pi-coding-agent?style=flat-square" /></a>
</p>

> This is the `python` branch: pi/2 cut down to Python. The TypeScript edition, with the full Pi framework, is on [`main`](https://github.com/windx987/pi-2).

# Lobotomized: pi/2 in Python

Lobotomized is a small Python version of pi/2, the Pi Workshop Edition. It follows the same eight steps as Pi, one file per step, in about 800 lines of standard-library Python. Its terminal looks and behaves like Pi's: the logo header, the editor between two borders, thinking in dim italics, tool calls in colored boxes, and the footer with tokens and model.

Like pi/2 it has no built-in tools. Every tool comes from an [extension](#extensions): you write `read`, `write`, `edit` and `bash` yourself, in [python/exercises/](python/exercises/).

## The big picture

What the original Pi does with one prompt, step by step, with the code that does each step. Lobotomized has the same steps in Python (see [the table below](#the-eight-steps-in-the-code)).

<p align="center"><img alt="The original Pi: 1 interactive mode reads your input, 2 AgentSession starts the agent and declares the tools, 3 the agent loop asks the model, 4 streamFn and ModelRuntime route the request, 5 the provider calls the LLM, 6 the arguments are validated and extensions see the call, 7 the tool's execute runs, 8 the result goes back to the model and is saved; the loop repeats while the model calls tools." src="./assets/diagrams/big-picture.svg" width="900"></p>

## Getting started

Requires Python 3.10 or newer and no packages, [Ollama](https://ollama.com) for the model, and Docker for exercise 04.

```bash
git clone -b python https://github.com/windx987/pi-2.git
cd pi-2
```

Pull the model and give it a 32k context (Ollama's default of 4096 tokens is too small and cuts requests without an error):

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

Then start it from the clone with the example tool, the way the TypeScript edition starts with `./pi-test.sh`:

```bash
./pi2.sh -e python/examples/hello.py
```

It starts with the first model in `models.json`. Type `/model` to list the others and `/model 2` to switch, or start with one: `./pi2.sh --model ollama/gemma4-workshop:12b`.

Ask it to greet someone. `pi2.sh` runs `python3 -m pi2` with `python/` on the module path and works from any directory; set `PYTHON` to use another interpreter. To get a `pi2` command instead, run `pip install -e python` once.

| Key or command | Does |
|---|---|
| Enter | Send the message |
| ctrl+c | While the agent works: stop it. In the editor: clear it |
| ctrl+d | Exit |
| `/model` | List the models in `models.json`; `/model <number>` or `/model <provider/id>` switches |
| `/new`, `/quit`, `/help` | New session, exit, list commands |

Text you type while the agent works waits in the editor for the next message.

## The eight steps in the code

| Step | Pi (TypeScript) | Lobotomized (Python) |
|---|---|---|
| 1. Interactive mode | `modes/interactive/interactive-mode.ts` | [python/pi2/tui.py](python/pi2/tui.py) `InteractiveMode.run` |
| 2. AgentSession | `core/agent-session.ts` | [python/pi2/session.py](python/pi2/session.py) `AgentSession.prompt` |
| 3. Agent loop | `packages/agent/src/agent-loop.ts` | [python/pi2/agent_loop.py](python/pi2/agent_loop.py) `run` |
| 4. streamFn and ModelRuntime | `core/sdk.ts`, `core/model-runtime.ts` | [python/pi2/model_runtime.py](python/pi2/model_runtime.py) `stream_fn` |
| 5. Provider → LLM | `packages/ai/src/api/openai-completions.ts` | [python/pi2/ai.py](python/pi2/ai.py) `stream` |
| 6. Validate, then ask extensions | `validateToolArguments`, `beforeToolCall` | [python/pi2/schema.py](python/pi2/schema.py), `AgentSession.before_tool_call` |
| 7. Tool runs | your extension's `execute()` | your extension's `execute()`, called in `agent_loop.execute_tool_call` |
| 8. Result back, saved | `currentContext.messages.push`, `appendMessage` | `agent_loop.run`, `AgentSession.save` |

Read them in that order. [python/pi2/extensions.py](python/pi2/extensions.py) is how [extensions](#extensions) get in, and [python/pi2/cli.py](python/pi2/cli.py) starts everything.

## Project structure

<p align="center"><img alt="Project structure of the python branch: python/pi2/ holds the agent, one file per step (cli.py, tui.py step 1, session.py steps 2 and 8, agent_loop.py step 3, model_runtime.py step 4, ai.py step 5, schema.py step 6, extensions.py). python/exercises/ holds your extensions 01-read to 04-bash and 05-subagent, python/examples/ hello.py and permission_gate.py. tests/, pyproject.toml, assets/ and the TypeScript packages/ and apps/ are outside the workshop path; education/ has the instructions for 01 to 04 and the playground." src="./assets/diagrams/python-structure.svg" width="760"></p>

You work in red: your extensions, and the instructions in [education/](education/). The blue files are pi2, numbered by the steps of [the big picture](#the-big-picture): start with [session.py](python/pi2/session.py) and [agent_loop.py](python/pi2/agent_loop.py). Grey parts are not needed for the workshop.

## Extensions

An extension is any Python file you load with `-e`. It has one function, `extension(pi)`, which pi2 calls at startup with an `ExtensionAPI`. Everything the model can do comes from extensions: pi2 itself contains no tools. Start it without `-e` and the model cannot read, write or run anything.

Through `pi`, an extension can do two things:

| Call | Does | Step |
|---|---|---|
| `pi.register_tool(tool)` | Offers a tool to the model. Its `execute(params, ctx)` runs when the model calls it | 2, 7 |
| `pi.on("tool_call", handler)` | Sees every tool call before it runs. `handler(call, args)` returns a reason to block it, or `None` | 6 |

So one file can add a tool, put a rule on other files' tools, or both. These are all the extensions in this branch:

| File | Kind | What it shows |
|---|---|---|
| [examples/hello.py](python/examples/hello.py) | tool | The smallest tool |
| [examples/permission_gate.py](python/examples/permission_gate.py) | listener | Blocks dangerous commands sent to the `bash` tool |
| [exercises/01-read](python/exercises/01-read/starter.py) to [04-bash](python/exercises/04-bash/starter.py) | tool | The four coding tools, which you write |
| [exercises/05-subagent](python/exercises/05-subagent/starter.py) | tool | A tool that runs a second agent through `ctx.session` |

A tool extension:

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

Load several with repeated `-e`; they work together. In Pi it is the same idea in TypeScript: `export default function (pi: ExtensionAPI)` with `pi.registerTool` and `pi.on("tool_call")`, and [about 70 example extensions](packages/coding-agent/examples/extensions/).

## Exercises

| Exercise | Tool | Instructions |
|---|---|---|
| [01-read](python/exercises/01-read/starter.py) | `read` | [README](education/exercises/01-read/README.md) |
| [02-write](python/exercises/02-write/starter.py) | `write` | [README](education/exercises/02-write/README.md) |
| [03-edit](python/exercises/03-edit/starter.py) | `edit` | [README](education/exercises/03-edit/README.md) |
| [04-bash](python/exercises/04-bash/starter.py) | `bash` | [README](education/exercises/04-bash/README.md) |
| [05-subagent](python/exercises/05-subagent/starter.py) | `subagent` | [README](python/exercises/05-subagent/README.md) (Python only) |

The READMEs for 01 to 04 are the TypeScript exercises'; the tasks are the same, and each starter's comments name the Python functions to use. Work in a copy of the playground under your home directory, never in the repository:

```bash
cp -R education/playground ~/pi-workshop && cd ~/pi-workshop
"$REPO/pi2.sh" -e "$REPO/python/exercises/01-read/starter.py"
```

`REPO` is the path of your clone. After each exercise, add the next file with another `-e`; type `/new` to start over.

## What Pi does that Lobotomized leaves out

It keeps the path of one prompt and drops the rest: one provider API (`openai-completions`, which covers Ollama), no Markdown rendering, no session resume, no compaction, no skills or slash-command extensions, no parallel tool calls, no image input. Sessions are saved to `~/.pi/agent/python-sessions/` but not loaded again.

## Tests

```bash
cd python
python -m unittest discover tests
```

The tests need no model: a fake stream function drives the agent loop, and a local HTTP server streams a recorded answer to the provider.

## License

MIT, as the original Pi.
