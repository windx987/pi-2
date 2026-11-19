# The edit tool: exact text replacements inside the working directory.
#
# Load all tools:  python3 -m pi2 -e tools
# Load only this:   python3 -m pi2 -e tools/edit.py

from pathlib import Path

from pi2 import ExtensionAPI, define_tool


def resolve_inside_cwd(ctx, path, action):
    cwd = Path(ctx.cwd).resolve()
    target = Path(path).expanduser()
    if not target.is_absolute():
        target = cwd / target
    target = target.resolve()
    try:
        target.relative_to(cwd)
    except ValueError as error:
        raise ValueError(
            f"Refusing to {action} {path}: only files inside the working directory may be changed."
        ) from error
    return target


def count_occurrences(text, needle):
    """Count matches including overlapping ones, so an ambiguous oldText is rejected."""
    count = 0
    start = 0
    while True:
        index = text.find(needle, start)
        if index == -1:
            return count
        count += 1
        start = index + 1


def find_matches(original, edits, path):
    if not edits:
        raise ValueError("edits is empty: give at least one replacement.")

    matches = []
    for index, edit in enumerate(edits):
        old = edit["oldText"]
        if old == "":
            raise ValueError(f"edits[{index}].oldText is empty. Give the exact text to replace.")

        count = count_occurrences(original, old)
        if count == 0:
            raise ValueError(
                f"edits[{index}].oldText was not found in {path}. Read the file again and copy the text exactly."
            )
        if count > 1:
            raise ValueError(
                f"edits[{index}].oldText occurs {count} times in {path}. "
                "Include more surrounding text to make it unique."
            )

        start = original.index(old)
        matches.append(
            {"index": index, "start": start, "end": start + len(old), "newText": edit["newText"]}
        )

    matches.sort(key=lambda match: match["start"])
    for previous, current in zip(matches, matches[1:]):
        if current["start"] < previous["end"]:
            raise ValueError(
                f"edits[{previous['index']}] and edits[{current['index']}] overlap. Merge them into one edit."
            )
    return matches


def execute_edit(params, ctx):
    target = resolve_inside_cwd(ctx, params["path"], "edit")
    try:
        original = target.read_text(encoding="utf-8")
    except FileNotFoundError as error:
        raise ValueError(f"File not found: {params['path']}") from error
    except IsADirectoryError as error:
        raise ValueError(f"Not a file: {params['path']}") from error
    except UnicodeDecodeError as error:
        raise ValueError(f"File is not UTF-8 text: {params['path']}") from error

    matches = find_matches(original, params["edits"], params["path"])
    updated = original
    for match in reversed(matches):
        updated = updated[: match["start"]] + match["newText"] + updated[match["end"] :]

    target.write_text(updated, encoding="utf-8")
    return f"Applied {len(matches)} edit(s) to {params['path']}"


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


def extension(pi: ExtensionAPI):
    pi.register_tool(edit_tool)
