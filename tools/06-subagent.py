from pi2 import ExtensionAPI, define_tool


def execute(params, ctx):
    # TODO: require a parent session and non-empty task
    # TODO: copy parent tools except subagent
    # TODO: run a child session and return its final text
    raise NotImplementedError


subagent_tool = define_tool(
    name="subagent",
    label="subagent",
    description="Delegate a self-contained task to another agent session.",
    parameters={
        "type": "object",
        "properties": {"task": {"type": "string"}},
        "required": ["task"],
    },
    execute=execute,
)


def extension(pi: ExtensionAPI):
    pi.register_tool(subagent_tool)
