# The workshop file: five tools. `hello` and `bash` work; read, write and edit are yours.
#
# Load it from python/:
#   python3 -m pi2 -e exercises/tools.py
#
# With a private settings file:
#   python3 -m pi2 --settings ../settings.local.json -e exercises/tools.py
#
# From a copy of the playground (~/pi-workshop):
#   PYTHONPATH="$REPO/python" python3 -m pi2 -e "$REPO/python/exercises/tools.py"
#
# The bash tool is a complete example. The comments on read, write and edit are the exercises.

import subprocess

from pi2 import ExtensionAPI, define_tool


def execute_hello(params, ctx):
    return f"Hello, {params['name']}!"


hello_tool = define_tool(
    name="hello",
    label="hello",
    description="Greet someone by name",
    parameters={"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]},
    execute=execute_hello,
)


def execute_read(params, ctx):
    # EXERCISE 1: Resolve params["path"] against ctx.cwd (os.path.join, or pathlib: Path(ctx.cwd) / path),
    # so relative paths mean "relative to the directory the agent works in".
    #
    # EXERCISE 2: Read the file as UTF-8 text (Path.read_text(encoding="utf-8")).
    #
    # EXERCISE 3: Apply params.get("offset") and params.get("limit"). Split into lines, keep the selected
    # ones, and when lines remain after them, end the text with a note such as
    # "[120 more lines. Use offset=201 to continue.]" so the model knows how to read on.
    #
    # EXERCISE 4: Errors. Raise an exception for a missing file or an offset past the end of the file.
    # pi2 turns a raised exception into an error result; write the message for the model, which reads it.
    #
    # Return the text as a string.
    #
    # CHALLENGE: Large files. Cap the output (for example 2000 lines or 50 KB) and say so in the text.
    raise NotImplementedError(f"read is not implemented yet (asked for {params['path']} in {ctx.cwd}).")


read_tool = define_tool(
    # The name is part of the contract: models are trained on tools called "read".
    name="read",
    label="read",
    description=(
        "Read the contents of a text file. Use offset and limit to read part of a large file; "
        "offset is the first line to read, starting at 1."
    ),
    prompt_snippet="Read file contents",
    prompt_guidelines=["Use read to examine files instead of cat or sed."],
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Path to the file, relative to the working directory or absolute"},
            "offset": {"type": "number", "description": "Line number to start reading from (1-indexed)"},
            "limit": {"type": "number", "description": "Maximum number of lines to read"},
        },
        "required": ["path"],
    },
    execute=execute_read,
)


def execute_write(params, ctx):
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
    execute=execute_write,
)


def execute_edit(params, ctx):
    # EXERCISE 1: Resolve params["path"] against ctx.cwd and read the file as UTF-8.
    #
    # EXERCISE 2: For each edit, find edit["oldText"] in the ORIGINAL content (not in the result of the
    # previous edit). Raise an exception when it occurs zero times or more than once (str.count);
    # include which edit failed (edits[0], edits[1], ...) so the model can fix that one.
    #
    # EXERCISE 3: Reject overlapping edits, then apply all replacements. Apply from the end of the
    # file to the start, so earlier positions stay valid.
    #
    # EXERCISE 4: Write the new content and return a confirmation. For a diff in the result, see
    # difflib.unified_diff.
    #
    # CHALLENGE: Windows line endings. A file with CRLF line endings does not contain an oldText the
    # model wrote with LF. Match on LF-normalized text and write CRLF back.
    raise NotImplementedError(f"edit is not implemented yet (asked for {params['path']} in {ctx.cwd}).")


edit_tool = define_tool(
    name="edit",
    label="edit",
    description=(
        "Edit a file with exact text replacements. Each edits[].oldText must match exactly one place "
        "in the original file; edits must not overlap."
    ),
    prompt_snippet="Make precise file edits with exact text replacement, including multiple disjoint edits in one call",
    prompt_guidelines=["Use edit for targeted changes. Batch changes to one file in a single call."],
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Path to the file, relative to the working directory or absolute"},
            "edits": {
                "type": "array",
                "description": "One or more replacements, each matched against the original file",
                "items": {
                    "type": "object",
                    "properties": {
                        "oldText": {"type": "string", "description": "Exact text to replace; must occur once in the original file"},
                        "newText": {"type": "string", "description": "Replacement text"},
                    },
                    "required": ["oldText", "newText"],
                },
            },
        },
        "required": ["path", "edits"],
    },
    execute=execute_edit,
)


def execute_bash(params, ctx):
    """Run the command on the host, in the working directory."""
    # Commands run as your user, on your machine. There is no sandbox here: the model can do
    # anything you can. Work in a copy of the playground, not in the repository.
    try:
        result = subprocess.run(
            ["bash", "-c", params["command"]],
            cwd=ctx.cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=params.get("timeout"),
        )
    except subprocess.TimeoutExpired as error:
        raise RuntimeError("Command stopped after the timeout.") from error
    output = result.stdout
    if result.returncode != 0:
        raise RuntimeError(f"{output}\nCommand exited with code {result.returncode}")
    return output


bash_tool = define_tool(
    name="bash",
    label="bash",
    description=(
        "Execute a bash command in the working directory. Returns stdout and stderr combined. "
        "Optionally provide a timeout in seconds."
    ),
    prompt_snippet="Execute bash commands (ls, grep, find, etc.)",
    parameters={
        "type": "object",
        "properties": {
            "command": {"type": "string", "description": "Bash command to execute"},
            "timeout": {"type": "number", "description": "Timeout in seconds (optional, no default timeout)"},
        },
        "required": ["command"],
    },
    execute=execute_bash,
)


def extension(pi: ExtensionAPI):
    pi.register_tool(hello_tool)
    pi.register_tool(read_tool)
    pi.register_tool(write_tool)
    pi.register_tool(edit_tool)
    pi.register_tool(bash_tool)
