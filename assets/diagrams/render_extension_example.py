# Renders extension-example.svg: the code of two example extensions on the left, with the lines each step
# uses highlighted, and on the right what happens at each step when you ask "Greet Ada.".
# Reads the real files, so the image stays in sync with them. Usage: python3 render_extension_example.py
import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).with_name("extension-example.svg")

SANS = "-apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace"
STEP_COLORS = {"start": "#b03a37", "1": "#6b7280", "2": "#2f5a96", "3–5": "#6b7280", "6": "#6d4bb3", "7": "#2f7d5b", "8": "#9a6700"}
TINTS = {"start": "#fbeeee", "2": "#eef3fa", "6": "#f3effa", "7": "#eaf5ef", "8": "#fdf5e4"}

CODE_X, CODE_W = 40, 880
LINE_H = 22
CHAR_W = 7.3  # 12px monospace, with room for wider fonts


def find(lines, text):
    """1-based number of the only line that starts with text (after indentation)."""
    found = [i + 1 for i, line in enumerate(lines) if line.strip().startswith(text)]
    assert len(found) == 1, (text, found)
    return found[0]


def code_rows():
    """(file title, [(line number or None, text, [steps])]) for both panels."""
    hello = (ROOT / "examples/hello.py").read_text().splitlines()
    first = find(hello, "from pi2 import")
    steps = {
        find(hello, "def execute"): ["7"],
        find(hello, "return f\"Hello"): ["7", "8"],
        find(hello, "name=\"hello\""): ["2"],
        find(hello, "description="): ["2"],
        find(hello, "parameters="): ["2", "6"],
        find(hello, "def extension"): ["start"],
        find(hello, "pi.register_tool"): ["start"],
    }
    hello_rows = [(n, hello[n - 1], steps.get(n, [])) for n in range(first, len(hello) + 1)]

    gate = (ROOT / "examples/permission_gate.py").read_text().splitlines()
    start = find(gate, "def on_tool_call")
    gate_rows = [(n, gate[n - 1], ["6"] if n in (start, start + 2, start + 3) else []) for n in range(start, start + 4)]
    gate_rows.append((None, "    ...", []))
    gate_rows.append((None, "", []))
    ext = find(gate, "def extension")
    gate_rows += [(ext, gate[ext - 1], ["start"]), (ext + 1, gate[ext], ["start"])]
    return [("examples/hello.py", hello_rows), ("examples/permission_gate.py (part)", gate_rows)]


KEYWORDS = r"\b(from|import|def|return|if|for|in|None|not)\b"
TOKEN = re.compile(r'(?P<comment>#.*)|(?P<string>f?"""[^"]*"""|f?"[^"]*"|r?\'[^\']*\')|(?P<kw>' + KEYWORDS[2:-2] + r')\b|(?P<call>\b[a-z_]+(?=\())')
COLORS = {"comment": "#6e7781", "string": "#0a3069", "kw": "#cf222e", "call": "#8250df"}


def highlight(text):
    """Python source as SVG tspans with simple syntax colors; leading spaces kept as no-break spaces."""
    out, pos = [], 0
    for match in TOKEN.finditer(text):
        out.append(html.escape(text[pos:match.start()]))
        kind = match.lastgroup
        out.append(f'<tspan fill="{COLORS[kind]}">{html.escape(match.group())}</tspan>')
        pos = match.end()
    out.append(html.escape(text[pos:]))
    line = "".join(out)
    indent = len(line) - len(line.lstrip(" "))
    return "&#160;" * indent + line[indent:]


# Each image numbers its own steps 1, 2, 3, ... in the order of its run. Steps are keyed by the label they have
# in the code ("start", "2", "3–5", ...); write_svg fills this with the number each one shows.
SHOWN = {}


def badge_width(label):
    shown = SHOWN.get(label, label)
    return 18 if len(shown) == 1 else 12 + len(shown) * 6.5


def badge(x, y, label):
    """A step badge centred at (x, y): a circle, or a pill for longer labels."""
    width = badge_width(label)
    shape = f'<rect x="{x - width / 2:.1f}" y="{y - 9}" width="{width:.1f}" height="18" rx="9" fill="{STEP_COLORS[label]}"/>'
    text = f'<text x="{x:.1f}" y="{y + 4}" text-anchor="middle" fill="#fff" font-family="{SANS}" font-size="11" font-weight="700">{SHOWN.get(label, label)}</text>'
    return shape + text


def render_code(y, panels):
    """Code panels, each (title, rows), stacked from y. Returns the SVG parts and the bottom."""
    parts = []
    for title, rows in panels:
        parts.append(f'<text x="{CODE_X}" y="{y}" fill="#1a2b45" font-family="{MONO}" font-size="13" font-weight="700">{title}</text>')
        top = y + 10
        height = len(rows) * LINE_H + 16
        parts.append(f'<rect x="{CODE_X}" y="{top}" width="{CODE_W}" height="{height}" rx="10" fill="#f6f8fa" stroke="#d0d7de"/>')
        for i, (number, text, steps) in enumerate(rows):
            row_y = top + 8 + i * LINE_H
            base = row_y + 15
            if steps:
                parts.append(f'<rect x="{CODE_X + 1}" y="{row_y}" width="{CODE_W - 2}" height="{LINE_H}" fill="{TINTS[steps[0]]}"/>')
                parts.append(f'<rect x="{CODE_X + 1}" y="{row_y}" width="4" height="{LINE_H}" fill="{STEP_COLORS[steps[0]]}"/>')
                right = CODE_X + 86
                for label in reversed(steps):
                    width = badge_width(label)
                    parts.append(badge(right - width / 2, row_y + LINE_H / 2, label))
                    right -= width + 4
            if number:
                parts.append(f'<text x="{CODE_X + 112}" y="{base}" text-anchor="end" fill="#8c959f" font-family="{MONO}" font-size="12">{number}</text>')
            fill = "#8c959f" if number is None else "#1f2328"
            parts.append(f'<text x="{CODE_X + 124}" y="{base}" fill="{fill}" font-family="{MONO}" font-size="12">{highlight(text)}</text>')
            assert CODE_X + 124 + len(text) * CHAR_W < CODE_X + CODE_W, ("line too long", text)
        y = top + height + 40
    return parts, y - 40


RUN_X, RUN_W = 950, 430
RUN = [
    ("start", "You start pi2 with both files", ["./pi2.sh -e examples/hello.py \\", "  -e examples/permission_gate.py"],
     "Each extension(pi) runs: hello.py registers the hello tool, permission_gate.py adds a listener."),
    ("1", "You type: Greet Ada.", [], "Interactive mode hands it to AgentSession.prompt. No extension code runs."),
    ("2", "pi2 offers hello to the model", ['"hello": "Greet someone by name"', 'parameters: {"name": string}, required'],
     "From define_tool: the model sees only this, never your code."),
    ("3–5", "The model answers with a tool call", ['hello({"name": "Ada"})'], "Agent loop, model runtime and provider; no extension code."),
    ("6", "Checked, then the listener sees it", ['"Ada" is a string: matches parameters', 'on_tool_call: name is "hello", not "bash"'],
     "The listener returns None, so the call may run."),
    ("7", "Your tool runs", ['execute({"name": "Ada"}, ctx)', '→ "Hello, Ada!"'], "What execute returns becomes the tool result."),
    ("8", "The result goes back to the model", ['tool result: "Hello, Ada!"'], "The model reads it and answers you, or calls another tool."),
]


def wrap(text, width):
    words, lines, line = text.split(), [], ""
    for word in words:
        if line and len(line) + 1 + len(word) > width:
            lines.append(line)
            line = word
        else:
            line = f"{line} {word}".strip()
    return lines + [line]


def render_run(y, heading, run):
    """The step boxes of one run, under a heading. Returns the SVG parts and the bottom."""
    parts = [f'<text x="{RUN_X}" y="{y}" fill="#1a2b45" font-family="{SANS}" font-size="15" font-weight="700">{html.escape(heading, quote=False)}</text>']
    y += 14
    for label, title, code, note in run:
        notes = wrap(note, 56)
        height = 36 + len(code) * 19 + len(notes) * 18 + 8
        color = STEP_COLORS[label]
        parts.append(f'<rect x="{RUN_X}" y="{y}" width="{RUN_W}" height="{height}" rx="10" fill="{TINTS.get(label, "#ffffff")}" stroke="{color}" stroke-width="1.5"/>')
        width = badge_width(label)
        parts.append(badge(RUN_X + 16 + width / 2, y + 22, label))
        parts.append(f'<text x="{RUN_X + 26 + width}" y="{y + 27}" fill="#1a2b45" font-family="{SANS}" font-size="15" font-weight="700">{html.escape(title)}</text>')
        line_y = y + 52
        for text in code:
            # Descriptions in code font, not Python: no syntax colors, only the indentation kept.
            plain = html.escape(text)
            plain = "&#160;" * (len(plain) - len(plain.lstrip(" "))) + plain.lstrip(" ")
            parts.append(f'<text x="{RUN_X + 18}" y="{line_y}" fill="#1f2328" font-family="{MONO}" font-size="12">{plain}</text>')
            line_y += 19
        for text in notes:
            parts.append(f'<text x="{RUN_X + 18}" y="{line_y}" fill="#4b5563" font-family="{SANS}" font-size="13">{html.escape(text)}</text>')
            line_y += 18
        y += height + 10
    return parts, y - 10


def write_svg(out, panels, heading, run):
    """Write one example: code panels on the left, the run on the right."""
    SHOWN.clear()
    SHOWN.update({label: str(i + 1) for i, (label, *_) in enumerate(run)})
    code, code_bottom = render_code(48, panels)
    steps, run_bottom = render_run(38, heading, run)
    height = max(code_bottom, run_bottom) + 40
    width = RUN_X + RUN_W + 40
    head = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" font-family="{SANS}" font-size="14">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
    ]
    out.write_text("\n".join(head + code + steps + ["</svg>", ""]))
    print(f"wrote {out.name} ({width}x{height})")


def main():
    write_svg(OUT, code_rows(), 'What happens when you ask "Greet Ada."', RUN)


if __name__ == "__main__":
    main()
