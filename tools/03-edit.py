from pi2 import ExtensionAPI, define_tool


def execute(params, ctx):
    # TODO: resolve path and keep it inside cwd
    # TODO: require one oldText match
    # TODO: replace and write UTF-8
    raise NotImplementedError


edit_tool = define_tool(
    name="edit",
    label="edit",
    description="Replace one exact text fragment inside a working-directory file.",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "oldText": {"type": "string"},
            "newText": {"type": "string"},
        },
        "required": ["path", "oldText", "newText"],
    },
    execute=execute,
)


def extension(pi: ExtensionAPI):
    pi.register_tool(edit_tool)
