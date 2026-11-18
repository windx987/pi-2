# Exercise 05: the subagent tool. Lets the agent hand a task to a second agent with its own context.
#
# Load it with your read tool (the subagent uses the tools you load):
#   ./pi2.sh -e exercises/01-read/starter.py -e exercises/05-subagent/starter.py
# Then ask: "Use a subagent to find out what each file in this directory does."
#
# LEARN:
# Every file the agent reads stays in its messages and is sent again with each request, until the
# context window is full. A subagent is a second AgentSession with an empty message list. It does the
# reading in its own context and returns only its final answer, so the parent's context grows by one
# tool result instead of every file. To the parent it is just a tool: step 7, whose execute() happens
# to run steps 2 to 8 again.
#
# TRACE:
# pi2/session.py      AgentSession.prompt()   (what the subagent runs)
# Pi's version runs a separate `pi` process per task:
#   https://github.com/windx987/pi-2/blob/main/packages/coding-agent/examples/extensions/subagent/index.ts

from pi2 import ExtensionAPI, define_tool
from pi2.session import AgentSession


def execute(params, ctx):
    # ctx.session is the AgentSession running this tool: ctx.session.runtime, .model, .extensions,
    # .agent_dir.
    #
    # EXERCISE 1: The subagent's tools. Create an ExtensionAPI() and register every tool of
    # ctx.session.extensions.tools except "subagent" itself, so a subagent cannot start another one
    # (and that one another, without end).
    #
    # EXERCISE 2: Start the subagent: AgentSession(runtime, model, your ExtensionAPI, ctx.cwd, agent_dir),
    # then child.prompt(params["task"]). prompt() returns when the subagent's loop is done.
    #
    # EXERCISE 3: Return its answer. The last message in child.messages is its final answer; join the
    # text of its blocks whose "type" is "text". Add a short note on what it cost, such as
    # "[subagent: 4 tool calls, 3.1k input tokens]" (count "toolResult" messages, read child.usage).
    #
    # EXERCISE 4: Failures. When the last message's "stop_reason" is "error", raise an exception with
    # its "error_message". When it is "aborted" (you pressed ctrl+c), raise KeyboardInterrupt, so the
    # parent stops too instead of carrying on without the answer.
    #
    # CHALLENGE: Roles. Add a "role" parameter, "scout" or "worker", as Pi's example does with
    # agents/*.md: a scout gets only the read tool, a worker gets all of them.
    raise NotImplementedError(f"subagent is not implemented yet (asked: {params['task']}).")


subagent_tool = define_tool(
    name="subagent",
    label="subagent",
    description=(
        "Delegate a self-contained task to a subagent with its own, empty context. It can use your other "
        "tools and returns only its final answer. Describe the task fully: it does not see this conversation."
    ),
    prompt_snippet="Delegate a self-contained task to a subagent with a separate context",
    prompt_guidelines=["Use subagent for tasks that need many reads, such as surveying files; you get back only its summary."],
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
