# Exercise 04: the edit tool. Lets the agent change part of a file without rewriting all of it.
#
# Load it with the earlier tools (bash needs Docker; leave it out to try edit alone):
#   ./pi2.sh -e exercises/01-read/starter.py -e exercises/02-write/starter.py \
#     -e exercises/03-bash/starter.py -e exercises/04-edit/starter.py
# Then ask: "Rename the function add to sum in math.js."
#
# LEARN:
# The model never sees line numbers it can trust, so it names the text to replace. That only works
# when the text matches exactly once: zero matches means the model's view of the file is stale, two
# means the edit is ambiguous. Both must be errors, never guesses.

from pi2 import ExtensionAPI, define_tool


def execute(params, ctx):
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
    execute=execute,
)


def extension(pi: ExtensionAPI):
    pi.register_tool(edit_tool)
