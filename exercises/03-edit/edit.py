# Exercise 03: the edit tool. Lets the agent change part of a file without rewriting all of it.
#
# Load it with the read tool so you can inspect the file first:
#   python3 -m pi2 --cwd playground/03-edit \
#     -e exercises/01-read/read.py -e exercises/03-edit/edit.py
#
# Then ask: "Fix the bug in math.py."
#
# LEARN:
# The model does not see reliable line numbers, so it names the text to replace. That only works
# when the text matches exactly once: zero matches means the file changed; two matches means the
# edit is ambiguous. Both must be errors, never guesses.

from pathlib import Path

from pi2 import ExtensionAPI, define_tool


def execute(params, ctx):
    # EXERCISE 1: resolve params["path"] against ctx.cwd and refuse paths outside ctx.cwd.
    #
    # EXERCISE 2: read the file as UTF-8 text. Raise if oldText is empty.
    #
    # EXERCISE 3: count occurrences of params["oldText"]. It must appear exactly once. Raise with a
    # message that says whether it appeared zero times or more than once.
    #
    # EXERCISE 4: replace it with params["newText"], write the file back as UTF-8, and return a
    # confirmation. A failed edit must leave the file unchanged.
    raise NotImplementedError("edit is not implemented yet.")


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
