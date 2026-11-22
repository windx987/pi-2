from pi2 import ExtensionAPI, define_tool


def execute(params, ctx):
    # TODO: run the command in ctx.cwd using the host shell
    # TODO: combine stdout and stderr
    # TODO: report non-zero exit codes
    raise NotImplementedError


command_tool = define_tool(
    name="command",
    label="command",
    description="Run a command in the working directory using the host shell.",
    parameters={
        "type": "object",
        "properties": {"command": {"type": "string"}},
        "required": ["command"],
    },
    execute=execute,
)


def extension(pi: ExtensionAPI):
    pi.register_tool(command_tool)
