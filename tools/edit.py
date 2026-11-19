# The edit tool: one exact text replacement inside the working directory.

from pathlib import Path

from pi2 import ExtensionAPI, define_tool


def path_in_cwd(ctx, path):
    cwd = Path(ctx.cwd).resolve()
    target = (cwd / Path(path).expanduser()).resolve()
    if cwd not in target.parents:
        raise ValueError(f"Path is outside the working directory: {path}")
    return target


def execute(params, ctx):
    target = path_in_cwd(ctx, params["path"])
    text = target.read_text(encoding="utf-8")
    old = params["oldText"]
    if not old:
        raise ValueError("oldText is empty.")
    if text.count(old) != 1:
        raise ValueError(f"oldText must appear exactly once in {params['path']}.")
    target.write_text(text.replace(old, params["newText"], 1), encoding="utf-8")
    return f"Edited {params['path']}"


edit_tool = define_tool(
    name="edit",
    label="edit",
    description="Edit a file with one exact text replacement. oldText must appear exactly once in the file.",
    prompt_snippet="Make a precise file edit with exact text replacement",
    prompt_guidelines=["Use edit for targeted changes."],
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Path to the file, relative to the working directory or absolute"},
            "oldText": {"type": "string", "description": "Exact text to replace; must occur once in the file"},
            "newText": {"type": "string", "description": "Replacement text"},
        },
        "required": ["path", "oldText", "newText"],
    },
    execute=execute,
)


def extension(pi: ExtensionAPI):
    pi.register_tool(edit_tool)
