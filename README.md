<p align="center">
  <img alt="pi/2 logo" src="./assets/logo.svg" width="128">
</p>
<p align="center">
  <a href="https://discord.com/invite/3cU7Bz4UPx"><img alt="Discord" src="https://img.shields.io/badge/discord-community-5865F2?style=flat-square&logo=discord&logoColor=white" /></a>
  <a href="https://www.npmjs.com/package/@earendil-works/pi-coding-agent"><img alt="npm" src="https://img.shields.io/npm/v/@earendil-works/pi-coding-agent?style=flat-square" /></a>
</p>

> This is the `python` branch: only the Python version of pi/2. The TypeScript edition, with the full Pi framework it is modelled on, is on [`main`](https://github.com/windx987/pi-2).

# Lobotomized: pi/2 in Python

Lobotomized is a small Python version of pi/2, the Pi Workshop Edition. It follows the same eight steps as Pi, one file per step, in about 1,000 lines of standard-library Python. Its terminal looks and behaves like Pi's: the logo header, the editor between two borders, thinking in dim italics, tool calls in colored boxes, and the footer with tokens and model.

Like pi/2 it has no built-in tools. Every tool comes from an [extension](#extensions): you write `read`, `write`, `edit` and `bash` yourself, in [exercises/](exercises/).

## Getting started

Requires Python 3.10 or newer and no packages, a model served by [Ollama](https://ollama.com) or [vLLM](https://docs.vllm.ai), and Docker for exercise 03.

```bash
git clone -b python https://github.com/windx987/pi-2.git
cd pi-2
```

Connect a model: run it with Ollama or vLLM, give it a context of at least 32k tokens, and add it to `~/.pi/agent/models.json`, the same file Pi uses. [docs/models.md](docs/models.md) has both setups, step by step.

Then start it from the clone with the example tool, the way the TypeScript edition starts with `./pi-test.sh`:

```bash
./pi2.sh -e examples/hello.py
```

It starts with the first model in `models.json`. Type `/model` to list the others and `/model 2` to switch, or start with one: `./pi2.sh --model ollama/gemma4-workshop:12b`.

Ask it to greet someone. `pi2.sh` runs `python3 -m pi2` from the clone and works from any directory; set `PYTHON` to use another interpreter. To get a `pi2` command instead, run `pip install -e .` once.

| Key or command | Does |
|---|---|
| Enter | Send the message |
| ctrl+c | While the agent works: stop it. In the editor: clear it |
| ctrl+d | Exit |
| `/model` | List the models in `models.json`; `/model <number>` or `/model <provider/id>` switches |
| `/compact [focus]` | Summarize the older messages now to free context; the optional text says what the summary must keep. See [docs/compaction.md](docs/compaction.md) |
| `/context` | Show how full the context window is, where compaction starts, and what fills it. See [docs/compaction.md](docs/compaction.md) |
| `/new`, `/quit`, `/help` | New session, exit, list commands |

Text you type while the agent works waits in the editor for the next message.

## The big picture

What the original Pi does with one prompt, step by step, with the code that does each step. Lobotomized has the same steps in Python (see [the table below](#the-eight-steps-in-the-code)).

<p align="center"><img alt="The original Pi: 1 interactive mode reads your input, 2 AgentSession starts the agent and declares the tools, 3 the agent loop asks the model, 4 streamFn and ModelRuntime route the request, 5 the provider calls the LLM, 6 the arguments are validated and extensions see the call, 7 the tool's execute runs, 8 the result goes back to the model and is saved; the loop repeats while the model calls tools." src="./assets/diagrams/big-picture.svg" width="900"></p>

## The eight steps in the code

| Step | Pi (TypeScript) | Lobotomized (Python) |
|---|---|---|
| 1. Interactive mode | [`modes/interactive/interactive-mode.ts`](https://github.com/windx987/pi-2/blob/main/packages/coding-agent/src/modes/interactive/interactive-mode.ts) | [pi2/tui.py](pi2/tui.py) `InteractiveMode.run` |
| 2. AgentSession | [`core/agent-session.ts`](https://github.com/windx987/pi-2/blob/main/packages/coding-agent/src/core/agent-session.ts) | [pi2/session.py](pi2/session.py) `AgentSession.prompt` |
| 3. Agent loop | [`packages/agent/src/agent-loop.ts`](https://github.com/windx987/pi-2/blob/main/packages/agent/src/agent-loop.ts) | [pi2/agent_loop.py](pi2/agent_loop.py) `run` |
| 4. streamFn and ModelRuntime | `core/sdk.ts`, `core/model-runtime.ts` | [pi2/model_runtime.py](pi2/model_runtime.py) `stream_fn` |
| 5. Provider → LLM | [`packages/ai/src/api/openai-completions.ts`](https://github.com/windx987/pi-2/blob/main/packages/ai/src/api/openai-completions.ts) | [pi2/ai.py](pi2/ai.py) `stream` |
| 6. Validate, then ask extensions | `validateToolArguments`, `beforeToolCall` | [pi2/schema.py](pi2/schema.py), `AgentSession.before_tool_call` |
| 7. Tool runs | your extension's `execute()` | your extension's `execute()`, called in `agent_loop.execute_tool_call` |
| 8. Result back, saved | `currentContext.messages.push`, `appendMessage` | `agent_loop.run`, `AgentSession.save` |

Read them in that order. [pi2/extensions.py](pi2/extensions.py) is how [extensions](#extensions) get in, and [pi2/cli.py](pi2/cli.py) starts everything.

## Architecture

<p align="center"><img alt="Architecture of pi2: you talk to tui.py, which calls prompt() on session.py (AgentSession) and gets events back. The session runs agent_loop.py, which checks arguments with schema.py, calls your extensions' execute(params, ctx), and asks the model through model_runtime.py and ai.py, which streams from the LLM server. When the context fills up, the session has compaction.py summarize the older messages. cli.py loads your extension files into extensions.py, whose tools and handlers the session uses. The session saves messages and the runtime reads models.json, both in ~/.pi/agent." src="./assets/diagrams/architecture.svg" width="900"></p>

Each module knows only its neighbours. `tui.py` talks only to the session. `agent_loop.py` knows no terminal and no provider: it gets `stream_fn` and `before_tool_call` from the session, and reports everything through `emit(event)`. `model_runtime.py` turns a model from `models.json` into a request for `ai.py`, the only module that speaks HTTP. Your extensions come in through `extensions.py` only. Pi has the same split across its packages: see [its architecture](https://github.com/windx987/pi-2#architecture) on `main`.

## How a request becomes a tool call

<p align="center"><img alt="Sequence of one request: you type in tui.py, which calls AgentSession.prompt; the session runs agent_loop.run. In a loop until an answer has no tool calls: the loop calls stream_fn, model_runtime.py and ai.py send POST /chat/completions to the LLM server and stream back text, thinking and tool calls; events go to the session, which saves finished messages, and on to tui.py, which draws them. Then the loop validates the arguments (step 6), calls before_tool_call so every tool_call listener can block the call (step 6), calls your tool's execute(params, ctx) (step 7), and emits the result, which joins the messages for the next request (step 8). After the tool results, prepare_next_turn() lets the session compact if the context is over the threshold: compaction.py asks the model for a summary of the older messages, and the messages become the summary plus the newest ones. The session checks the same before the prompt. At the end the session gets agent_end and you see the answer." src="./assets/diagrams/request-sequence.svg" width="900"></p>

The numbers are the steps of [the big picture](#the-big-picture). The loop box repeats once per model answer: the conversation ends when the model answers without a tool call.

## Context length and compaction

Every request sends the whole conversation, so it grows with every tool result. When it nears the model's `contextWindow`, [compaction.py](pi2/compaction.py) asks the model to summarize the older messages and keeps only the summary and the newest ones, as Pi does. `/context` shows what fills the window, and `/compact [focus]` compacts by hand.

[docs/compaction.md](docs/compaction.md) explains when it happens, what is kept, what you see, and the settings.

## Project structure

<p align="center"><img alt="Project structure of the python branch, in four sections: the agent, your work, read and run, outside the workshop. pi2/ holds the agent, one file per step (cli.py, tui.py step 1, session.py steps 2 and 8, agent_loop.py step 3, model_runtime.py step 4, ai.py step 5, schema.py step 6, compaction.py, extensions.py). exercises/ holds your extensions 01-read to 04-edit and 05-subagent, each with a README and checks, and check.py, which runs the checks; examples/ has hello.py and permission_gate.py; playground/ has what the agent works on: a failing test and 30 incident reports; pi2.sh starts it; docs/ explains connecting a model and compaction. tests/, pyproject.toml and assets/ are outside the workshop path." src="./assets/diagrams/python-structure.svg" width="760"></p>

The four sections are the agent, your work, what you read and run, and what the workshop does not need. In the agent, the files have the colors of Pi's packages in [the big picture](#the-big-picture): blue for the app (coding-agent), purple for the loop (agent), green for what talks to the model (ai). The numbers are the big picture's steps: start with [session.py](pi2/session.py) and [agent_loop.py](pi2/agent_loop.py). You work in red: your extensions, their checks, and a copy of the [playground](playground/).

## Extensions

An extension is any Python file you load with `-e`. It has one function, `extension(pi)`, which pi2 calls at startup with an `ExtensionAPI`. Everything the model can do comes from extensions: pi2 itself contains no tools. Start it without `-e` and the model cannot read, write or run anything.

<p align="center"><img alt="Extensions in pi2. At startup: you start ./pi2.sh with -e files, cli.py creates an ExtensionAPI and loads each file, your file's extension(pi) runs and calls pi.register_tool (stored in pi.tools) or pi.on('tool_call') (stored in pi.handlers). At every request: step 1, you type a message and interactive mode hands it to AgentSession.prompt; step 2 offers every tool in pi.tools to the model; steps 3 to 5, the agent loop asks the model, which answers with a tool call; step 6 checks the arguments against the schema (wrong shape: error result, the tool does not run) and then every listener in pi.handlers sees the call (a returned reason blocks it: error result 'Blocked by extension'); step 7 runs tool.execute(params, ctx), where a return value is the result and an exception an error result; step 8 sends the result back to the model, which answers or calls another tool." src="./assets/diagrams/extensions.svg" width="900"></p>

Through `pi`, an extension can do two things:

| Call | Does | Step |
|---|---|---|
| `pi.register_tool(tool)` | Offers a tool to the model. Its `execute(params, ctx)` runs when the model calls it | 2, 7 |
| `pi.on("tool_call", handler)` | Sees every tool call before it runs. `handler(call, args)` returns a reason to block it, or `None` | 6 |

So one file can add a tool, put a rule on other files' tools, or both. These are all the extensions in this branch:

| File | Kind | What it shows |
|---|---|---|
| [examples/hello.py](examples/hello.py) | tool | The smallest tool |
| [examples/permission_gate.py](examples/permission_gate.py) | listener | Blocks dangerous commands sent to the `bash` tool |
| [exercises/01-read](exercises/01-read/read.py) to [04-edit](exercises/04-edit/edit.py) | tool | The four coding tools, which you write; 01 to 03 show the solution in the Steps of their README |
| [exercises/05-subagent](exercises/05-subagent/subagent.py) | tool | A tool that runs a second agent through `ctx.session` |

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

Load several with repeated `-e`; they work together. Here is one run with both kinds, step by step: the real `examples/hello.py` and `examples/permission_gate.py` on the left, each line highlighted with the step that uses it, and what happens when you ask "Greet Ada." on the right.

<p align="center"><img alt="One example, step by step. Left: the code of examples/hello.py and part of examples/permission_gate.py, with lines highlighted by step. Start: def extension(pi) with pi.register_tool(hello) in hello.py, and pi.on('tool_call', on_tool_call) in permission_gate.py. Step 2: name, description and parameters of define_tool, which the model sees. Step 6: parameters, which pi2 checks the arguments against, and on_tool_call, which returns None for a call that is not bash. Step 7: def execute(params, ctx). Step 8: its return value. Right: start, both files loaded; 1, you type Greet Ada.; 2, pi2 offers hello to the model; 3 to 5, the model answers hello({'name': 'Ada'}); 6, the arguments match and the listener lets the call run; 7, execute returns 'Hello, Ada!'; 8, the result goes back to the model." src="./assets/diagrams/extension-example.svg" width="900"></p>

In Pi it is the same idea in TypeScript: `export default function (pi: ExtensionAPI)` with `pi.registerTool` and `pi.on("tool_call")`, and [about 70 example extensions](https://github.com/windx987/pi-2/tree/main/packages/coding-agent/examples/extensions).

## Exercises

| Exercise | Tool | Instructions |
|---|---|---|
| [01-read](exercises/01-read/read.py) | `read` | [README](exercises/01-read/README.md) |
| [02-write](exercises/02-write/write.py) | `write` | [README](exercises/02-write/README.md) |
| [03-bash](exercises/03-bash/bash.py) | `bash` | [README](exercises/03-bash/README.md); with Docker running, the checks also use a real container |
| [04-edit](exercises/04-edit/edit.py) | `edit` | [README](exercises/04-edit/README.md) |
| [05-subagent](exercises/05-subagent/subagent.py) | `subagent` | [README](exercises/05-subagent/README.md) (not in the TypeScript edition) |

Each README says what the tool does, the steps, what to ask the agent and what you should see; the starter's comments name the Python functions to use. Work in a copy of the playground under your home directory, never in the repository:

```bash
cp -R "$REPO/playground" ~/pi-workshop && cd ~/pi-workshop
"$REPO/pi2.sh" -e "$REPO/exercises/01-read/read.py"
```

`REPO` is the path of your clone. After each exercise, add the next file with another `-e`; type `/new` to start over.

Check a tool without a model before you try it: `python3 exercises/check.py 01` runs the checks of exercise 01 against its `read.py` and shows PASS, FAIL or TODO for each step. `python3 exercises/check.py` checks all five, and `python3 exercises/check.py 01 path/to/my_read.py` checks another file.

## Playground

[playground/](playground/README.md) is what the agent works on, from a small project to more than one context can hold. Copy it under your home directory first, as above.

| Scenario | Tools | What it shows |
|---|---|---|
| [A failing test](playground/README.md#1-a-failing-test): `math.js` | read, write, bash, edit | The tool-call loop: read, run, fix, run again (exercises 01 to 04) |
| [Thirty incident reports](playground/README.md#2-thirty-incident-reports): `incidents/` | read, subagent | More than one context holds: subagents read, the parent gets the answers (exercise 05) |
| [Watching the context](playground/README.md#3-watching-the-context-context-compact-new): `incidents/` | read | `/context`, `/compact`, automatic compaction and `/new`, step by step |
| [A permission gate](playground/README.md#4-a-permission-gate): `examples/permission_gate.py` | read, write, bash, the gate | A listener blocks `rm -rf` and `sudo` before they run |

[playground/README.md](playground/README.md) has, for each scenario, a picture of what the agent does with a hint, why those tools fit, what to ask, and what to look for. `incidents/` is generated by [assets/playground/generate.py](assets/playground/generate.py); `--answers` prints the answers for the instructor.

## What Pi does that Lobotomized leaves out

It keeps the path of one prompt and drops the rest: one provider API (`openai-completions`, which covers Ollama and vLLM), no Markdown rendering, no session resume, simpler compaction (no split turns, no branch summaries, no extension hooks), no skills or slash-command extensions, no parallel tool calls, no image input. Sessions are saved to `~/.pi/agent/python-sessions/` but not loaded again.

## Tests

```bash
python3 -m unittest discover tests
```

The tests need no model: a fake stream function drives the agent loop, and a local HTTP server streams a recorded answer to the provider.

## License

MIT, as the original Pi.
