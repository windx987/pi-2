# How a request becomes a tool call

What happens between the moment you press Enter and the answer: which module calls which, and where your tool's `execute()` runs. The modules are in [Architecture](architecture.md).

<p align="center"><img alt="Sequence of one request: you type in tui.py, which calls AgentSession.prompt; the session runs agent_loop.run. In a loop until an answer has no tool calls: the loop calls stream_fn, model_runtime.py and ai.py send POST /chat/completions to the LLM server and stream back text, thinking and tool calls; events go to the session, which saves finished messages, and on to tui.py, which draws them. Then the loop validates the arguments, calls before_tool_call so every tool_call listener can block the call, calls your tool's execute(params, ctx), and emits the result, which joins the messages for the next request. After the tool results, prepare_next_turn() lets the session compact if the context is over the threshold: compaction.py asks the model for a summary of the older messages, and the messages become the summary plus the newest ones. The session checks the same before the prompt. At the end the session gets agent_end and you see the answer." src="../assets/diagrams/request-sequence.svg" width="900"></p>

The loop box repeats once per model answer: the conversation ends when the model answers without a tool call.

To read it in the code, start with `AgentSession.prompt` in [session.py](../pi2/session.py) and `run` in [agent_loop.py](../pi2/agent_loop.py). When the context fills up, the session compacts: see [compaction.md](compaction.md).
