# The write tool: create or overwrite a file inside the working directory.

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
    if target.is_dir():
        raise ValueError(f"Not a file: {params['path']}")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(params["content"], encoding="utf-8")
    return f"Wrote {params['path']}"


write_tool = define_tool(
    name="write",
    label="write",
    description="Write content to a file inside the working directory. Creates parent directories.",
    prompt_snippet="Create or overwrite files",
    prompt_guidelines=["Use write only for new files or complete rewrites."],
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Path to the file, relative to the working directory or absolute"},
            "content": {"type": "string", "description": "Content to write to the file"},
        },
        "required": ["path", "content"],
    },
    execute=execute,
)


def extension(pi: ExtensionAPI):
    pi.register_tool(write_tool)
