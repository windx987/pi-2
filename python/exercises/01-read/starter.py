# Exercise 01: the read tool. Lets the agent look at files in its working directory.
#
# Load it:  python -m pi2 -e exercises/01-read/starter.py
# Then ask: "What is in package.json?"
#
# LEARN:
# A tool is plain data plus one function. `define_tool` describes it to the model (name, description,
# JSON Schema of the arguments) and `pi.register_tool` hands it to pi2. From there pi2 does the rest:
# it declares the tool to the model, validates the model's arguments against `parameters`, calls
# `execute`, and sends what you return back to the model as the tool result.
#
# TRACE:
# pi2/session.py     AgentSession.prompt()       (the tools offered to the model)
# pi2/agent_loop.py  execute_tool_call()         (validation, execution, result)

from pi2 import ExtensionAPI, define_tool


def execute(params, ctx):
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
    execute=execute,
)


def extension(pi: ExtensionAPI):
    pi.register_tool(read_tool)
