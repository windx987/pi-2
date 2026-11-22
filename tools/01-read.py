from pi2 import ExtensionAPI, define_tool


def execute(params, ctx):
    # TODO: resolve path from ctx.cwd
    # TODO: read UTF-8 lines
    # TODO: apply offset and limit
    raise NotImplementedError


read_tool = define_tool(
    name="read",
    label="read",
    description="Read a UTF-8 text file with optional offset and limit.",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "offset": {"type": "number"},
            "limit": {"type": "number"},
        },
        "required": ["path"],
    },
    execute=execute,
)


def extension(pi: ExtensionAPI):
    pi.register_tool(read_tool)
