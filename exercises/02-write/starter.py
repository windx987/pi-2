# Exercise 02: the write tool. Lets the agent create files and replace them whole.
#
# Load it with the read tool:
#   ./pi2.sh -e exercises/01-read/starter.py -e exercises/02-write/starter.py
# Then ask: "Create notes/todo.md with three items."
#
# LEARN:
# The model fills `parameters` as JSON. pi2 validates that JSON against the schema before `execute`
# runs, so `params` here always has a string "path" and a string "content": you check only what the
# schema cannot say, such as where the file may be written.
#
# SAFETY:
# Whatever path the model sends is written. Decide which directories the agent may write to.

from pi2 import ExtensionAPI, define_tool


def execute(params, ctx):
    # EXERCISE 1: Resolve params["path"] against ctx.cwd.
    #
    # EXERCISE 2: Validation. Refuse paths outside ctx.cwd (Path.resolve(), then is_relative_to(cwd)).
    # Raise an exception that says why.
    #
    # EXERCISE 3: Create the parent directories (mkdir(parents=True, exist_ok=True)), then write the
    # content as UTF-8 (write_text).
    #
    # EXERCISE 4: Return a short confirmation, such as "Wrote 120 bytes to notes/todo.md". The model
    # does not see the file unless it reads it, so say what happened.
    raise NotImplementedError(f"write is not implemented yet (asked for {params['path']} in {ctx.cwd}).")


write_tool = define_tool(
    name="write",
    label="write",
    description=(
        "Write content to a file. Creates the file if it does not exist, overwrites it if it does, "
        "and creates parent directories."
    ),
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
