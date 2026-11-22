# Exercise 06: the subagent tool. Run a second agent with its own context.
#
# Load it with the read tool, because the subagent can only use the tools you load:
#   python3 -m pi2 --cwd playground/06-subagents \
#     -e exercises/01-read/read.py -e exercises/06-subagents/subagent.py
#
# Then ask it to split the incident reports between three subagents.
#
# LEARN:
# Every file the agent reads stays in its messages and is sent again with each request. A subagent
# is a second AgentSession with an empty message list: it does the reading in its own context and
# returns only its final answer, so the parent's context grows by one result instead of every file.

from pi2 import ExtensionAPI, define_tool
from pi2.session import AgentSession


def execute(params, ctx):
    # EXERCISE 1: ctx.session is the parent AgentSession. Get its runtime, model, tools and agent_dir.
    # Create a new ExtensionAPI and register every parent tool except "subagent" itself.
    #
    # EXERCISE 2: create AgentSession(parent.runtime, parent.model, child_extensions, ctx.cwd,
    # parent.agent_dir), then call child.prompt(params["task"]). The child starts with no messages.
    #
    # EXERCISE 3: if the child's last message has stop_reason "error", raise with its error_message.
    # If it is "aborted" (ctrl+c), raise KeyboardInterrupt so the parent stops too.
    #
    # EXERCISE 4: return the text blocks of the child's last message, plus a short cost note such as
    # "[subagent: 1 tool call, 3.0k input tokens]". Count toolResult messages and use child.usage.
    raise NotImplementedError("subagent is not implemented yet.")


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
