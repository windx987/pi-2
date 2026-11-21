# Renders exercise-NN-name.svg for each exercise with a solution: the starter with the solution from its
# README on the left, lines highlighted by the step that uses them, and on the right what happens when you
# ask the exercise's "Try it" question. Reads the real files, so the images stay in sync with them.
# Usage: python3 render_exercise_examples.py
import re
from pathlib import Path

from render_extension_example import CHAR_W, CODE_W, ROOT, STEP_COLORS, TINTS, write_svg

STEP_COLORS["2–8"] = "#6b7280"
TINTS["2–8"] = "#f3f4f6"
MAX_CHARS = int((CODE_W - 124) / CHAR_W)

# Lines that a step uses, by how the stripped line starts. Lines inside execute() add "execute" rules.
RULES = [
    ("def extension", ["start"]),
    ("pi.register_tool", ["start"]),
    ('name="', ["2"]),
    ("description=", ["2"]),
    ("parameters=", ["2", "6"]),
    ("def execute", ["7"]),
]
EXECUTE_RULES = [
    ("tools.register_tool", ["2"]),
    ("tools.on(", ["6"]),
    ("child.prompt", ["2–8"]),
    ("return ", ["7", "8"]),
    ("raise ", ["8"]),
]


def solution_source(name):
    """The exercise's tool file, such as read.py, with execute() replaced by the whole function from its README."""
    folder = ROOT / "exercises" / name
    readme = (folder / "README.md").read_text()
    code = re.search(r"```python\n(.*?)```", readme.split("The whole function")[1], re.S).group(1)
    imports, function = code.split("\n\n\n", 1)
    imports = "\n".join(line for line in imports.splitlines() if not line.startswith("#") and "pi2" not in line)
    starter = (folder / f"{name.split('-', 1)[1]}.py").read_text()
    start = starter.index("def execute(params, ctx):")
    end = starter.index("\n\n\n", start)
    source = starter[:start] + function.rstrip("\n") + starter[end:]
    if imports:
        # Standard-library imports go with the starter's own, above the blank line before pi2.
        before = "\n\nfrom pi2 import" if "import " in source.split("from pi2 import")[0] else "from pi2 import"
        source = source.replace(before, f"\n{imports}{before}" if before.startswith("\n") else f"{imports}\n\n{before}", 1)
    return source


def shorten(line):
    """Cut the longest string literal, or the end of a comment, so the line fits the panel, marking the cut with ….
    Only for the tool definition: the solution's code is shown whole."""
    if line.strip().startswith("#") and len(line) > MAX_CHARS:
        return line[:MAX_CHARS - 1].rstrip() + "…"
    while len(line) > MAX_CHARS:
        # A whole literal: an opening quote after a non-word character, up to the next quote.
        literal = max(re.finditer(r'(?<![\w\]])"([^"]{12,})"', line), key=lambda m: len(m.group(1)))
        keep = len(literal.group(1)) - (len(line) - MAX_CHARS) - 1
        line = line[:literal.start(1)] + literal.group(1)[:max(keep, 8)].rstrip() + "…" + line[literal.end(1):]
    return line


def code_rows(name, fold):
    """Rows for the code panel: from the imports to the end, without the exercise comments."""
    lines = solution_source(name).splitlines()
    first = next(i for i, line in enumerate(lines) if line.startswith(("import ", "from ")))
    rows, in_execute, folding = [], False, False
    for line in lines[first:]:
        stripped = line.strip()
        if line.startswith(("def ", "class ")) or (line and not line.startswith((" ", ")"))):
            in_execute = line.startswith("def execute")
            folding = any(line.startswith(prefix) for prefix in fold)
            if folding:
                rows.append((None, line, []))
                rows += [(None, "    ...", []), (None, "", [])]
                continue
        if folding:
            continue
        if stripped.startswith("#") and not in_execute:
            continue
        if not stripped and rows and not rows[-1][1].strip():
            continue
        rules = RULES + (EXECUTE_RULES if in_execute else [])
        steps = next((steps for prefix, steps in rules if stripped.startswith(prefix)), [])
        rows.append((None, line if in_execute and not stripped.startswith("#") else shorten(line), steps))
    while not rows[-1][1].strip():
        rows.pop()
    return rows


EXAMPLES = {
    "01-read": {
        "ask": "What is in package.json?",
        "run": [
            ("start", "You start pi2 with read", ["./pi2.sh -e exercises/01-read/read.py"],
             "extension(pi) runs and registers the read tool."),
            ("1", "You type the question", [], "Interactive mode hands it to AgentSession.prompt. No extension code runs."),
            ("2", "pi2 offers read to the model", ['"read": "Read the contents of a text file…"', "parameters: path required; offset, limit"],
             "From define_tool: the model sees only this, never your code."),
            ("3–5", "The model answers with a tool call", ['read({"path": "package.json"})'], "Agent loop, model runtime and provider."),
            ("6", "pi2 checks the arguments", ['"package.json" is a string: matches parameters'], "No offset or limit: both are optional."),
            ("7", "Your execute runs", ['Path(ctx.cwd) / "package.json"', "read_text → the whole file, no offset"],
             "A missing file raises FileNotFoundError instead."),
            ("8", "The result goes back to the model", ["tool result: the text of package.json"],
             "An exception would go back as an error result. The model answers you."),
        ],
    },
    "02-write": {
        "ask": "Create notes/todo.md with three items.",
        "run": [
            ("start", "You start pi2 with read and write", ["./pi2.sh -e exercises/01-read/read.py \\", "  -e exercises/02-write/write.py"],
             "Each extension(pi) registers its tool."),
            ("1", "You type the request", [], "Interactive mode hands it to AgentSession.prompt."),
            ("2", "pi2 offers read and write", ['"write": "Write content to a file…"', "parameters: path, content (both required)"],
             "From define_tool: the model sees only this, never your code."),
            ("3–5", "The model answers with a tool call", ['write({"path": "notes/todo.md",', '       "content": "- …\\n- …\\n- …\\n"})'],
             "Agent loop, model runtime and provider."),
            ("6", "pi2 checks the arguments", ["path and content are strings: matches parameters"],
             "A missing content would be an error result here, before execute."),
            ("7", "Your execute runs", ["resolve → <cwd>/notes/todo.md, inside cwd", "mkdir notes/, then write_bytes"],
             "notes/../../.bashrc would resolve outside cwd and be refused."),
            ("8", "The result goes back to the model", ['tool result: "Wrote <n> bytes to notes/todo.md"'],
             "The model does not see the file; the confirmation says it was written."),
        ],
    },
    "03-bash": {
        "ask": "Run the tests.",
        "fold": ["def docker_args", "LOCAL_RUNNER", "def no_docker", "def command_args"],
        "run": [
            ("start", "You start pi2 with three tools", ["pi2.sh -e …/01-read/read.py \\", "  -e …/02-write/write.py -e …/03-bash/bash.py"],
             "From a playground copy under your home directory, with Docker running."),
            ("1", "You type the request", [], "Interactive mode hands it to AgentSession.prompt."),
            ("2", "pi2 offers read, write and bash", ['"bash": "Execute a bash command in the…"', "parameters: command required; timeout"],
             "From define_tool: the model sees only this, never your code."),
            ("3–5", "The model answers with a tool call", ['bash({"command": "npm test"})'], "Agent loop, model runtime and provider."),
            ("6", "pi2 checks the arguments", ['"npm test" is a string: matches parameters'], "No timeout: communicate() waits until the end."),
            ("7", "Your execute runs", ["docker run --rm --network none … \\", '  bash -c "npm test"', "→ output, exit code 1"],
             "A new container sees only the playground, and is removed afterwards."),
            ("8", "The result goes back to the model", ["error result: the test output and", '"Command exited with code 1."'],
             "Red in the terminal. The model reads which test failed."),
        ],
    },
}


def main():
    for name, example in EXAMPLES.items():
        rows = code_rows(name, example.get("fold", []))
        out = Path(__file__).with_name(f"exercise-{name}.svg")
        write_svg(out, [(f"exercises/{name}/{name.split('-', 1)[1]}.py, solved", rows)], f'You ask: "{example["ask"]}"', example["run"])


if __name__ == "__main__":
    main()
