# Architecture

<p align="center"><img alt="Architecture of pi2: you talk to tui.py, which calls prompt() on session.py (AgentSession) and gets events back. The session runs agent_loop.py, which checks arguments with schema.py, calls your extensions' execute(params, ctx), and asks the model through model_runtime.py and ai.py, which streams from the LLM server. When the context fills up, the session has compaction.py summarize the older messages. cli.py loads your extension files into extensions.py, whose tools and handlers the session uses. The session saves messages and the runtime reads models.json, both in ~/.pi/agent." src="../assets/diagrams/architecture.svg" width="900"></p>

Each module knows only its neighbours. `tui.py` talks only to the session. `agent_loop.py` knows no terminal and no provider: it gets `stream_fn` and `before_tool_call` from the session, and reports everything through `emit(event)`. `model_runtime.py` turns a model from `models.json` into a request for `ai.py`, the only module that speaks HTTP. Your extensions come in through `extensions.py` only. Pi has the same split across its packages: see [its architecture](https://github.com/windx987/pi-2#architecture) on `main`.

Start reading with [session.py](../pi2/session.py) and [agent_loop.py](../pi2/agent_loop.py). [extensions.py](../pi2/extensions.py) is how [extensions](../README.md#extensions) get in, and [cli.py](../pi2/cli.py) starts everything.

[structure.md](structure.md) shows where each file is. [request.md](request.md) follows one request through these modules, step by step. [compaction.md](compaction.md) explains what happens when the conversation fills the model's context.
