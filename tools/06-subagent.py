# The subagent tool: run a second agent in its own context and return only its answer.

from pi2 import ExtensionAPI, define_tool
from pi2.session import AgentSession


def execute(params, ctx):
    task = params["task"]
    if not task.strip():
        raise ValueError("task is empty.")
    parent = ctx.session
    if parent is None:
        raise ValueError("subagent needs a running session.")

    # The subagent gets the parent's tools, but not subagent itself: no endless recursion.
    child_extensions = ExtensionAPI()
    for tool in parent.extensions.tools.values():
        if tool.name != "subagent":
            child_extensions.register_tool(tool)

    child = AgentSession(parent.runtime, parent.model, child_extensions, ctx.cwd, parent.agent_dir)
    child.prompt(task)

    last = child.messages[-1] if child.messages else {}
    if last.get("role") == "toolResult" and last.get("aborted"):
        raise KeyboardInterrupt
    if last.get("stop_reason") == "error":
        raise RuntimeError(last.get("error_message") or "the subagent failed")
    if last.get("stop_reason") == "aborted":
        raise KeyboardInterrupt

    content = last.get("content", [])
    if isinstance(content, list):
        text = "\n".join(
            block.get("text", "") for block in content if block.get("type") == "text"
        ).strip()
    else:
        text = str(content).strip()
    if not text:
        text = "(the subagent returned no text)"

    tool_calls = sum(1 for message in child.messages if message.get("role") == "toolResult")
    tokens = child.usage.get("input", 0)
    note = f"[subagent: {tool_calls} tool call{'s' if tool_calls != 1 else ''}, {tokens / 1000:.1f}k input tokens]"
    return f"{text}\n\n{note}"


subagent_tool = define_tool(
    name="subagent",
    label="subagent",
    description=(
        "Delegate a self-contained task to a subagent with its own, empty context. It can use your other "
        "tools and returns only its final answer. Describe the task fully: it does not see this conversation."
    ),
    prompt_snippet="Delegate a self-contained task to a subagent with a separate context",
    prompt_guidelines=[
        "Use subagent for tasks that need many reads, such as surveying files; you get back only its summary."
    ],
    parameters={
        "type": "object",
        "properties": {
            "task": {"type": "string", "description": "The complete task for the subagent, with all context it needs"},
        },
        "required": ["task"],
    },
    execute=execute,
)


def extension(pi: ExtensionAPI):
    pi.register_tool(subagent_tool)
