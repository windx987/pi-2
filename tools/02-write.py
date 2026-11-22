from pi2 import ExtensionAPI, define_tool


def execute(params, ctx):
    # TODO: resolve path from ctx.cwd
    # TODO: reject paths outside cwd
    # TODO: create parents and write UTF-8
    raise NotImplementedError


write_tool = define_tool(
    name="write",
    label="write",
    description="Write UTF-8 content inside the working directory.",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "content": {"type": "string"},
        },
        "required": ["path", "content"],
    },
    execute=execute,
)


def extension(pi: ExtensionAPI):
    pi.register_tool(write_tool)
