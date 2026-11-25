# Writes model-request.svg: the request pi2 sends to the model, each line tinted by where it comes from:
# pi2, you, or your extensions. Built with pi2's own code (session.py and ai.py) from the exercise tools,
# so the image stays in sync with them.
# Run from anywhere: python3 assets/diagrams/render_request.py
import json
import sys
import textwrap
from pathlib import Path

from render_playground import AMBER, BLUE, GREEN, RED, heading, hint, text

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from pi2 import ExtensionAPI, ai  # noqa: E402
from pi2.session import AgentSession  # noqa: E402

OUT = Path(__file__).with_name("model-request.svg")
WIDTH = 1240
SANS = "-apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"
MODEL = {"id": "gemma-4-12B-it-qat-w4a16-ct", "max_tokens": 8192}  # the workshop's Gemma 4 on vLLM
TOOLS = ["exercises/01-read/read.py", "exercises/02-write/write.py", "exercises/03-bash/bash.py"]
PROMPT = "Run the tests and tell me what fails."
CWD = "/Users/you/pi-2/playground"

CARD_X, CARD_W = 30, 360
PANEL_X, PANEL_W = 450, 760
LINE_H = 19
TOP = 70
CHARS = 94  # monospace characters that fit on a panel line
# Stronger tints than the other diagrams: here the color is the whole message.
YOU, EXT1, EXT2 = GREEN, AMBER, RED  # you; your tools in the system prompt; your tools entry
TINT = {BLUE: "#dce8f8", YOU: "#d3efdf", EXT1: "#fbe7b5", EXT2: "#f9d6d3"}


def request_lines():
    """The request body as (text, color) lines; color None is JSON structure."""
    api = ExtensionAPI()
    for path in TOOLS:
        api.load(str(ROOT / path))
    tools = list(api.tools.values())
    session = AgentSession.__new__(AgentSession)  # only for system_prompt(): no model, no files
    session.extensions, session.cwd = api, CWD
    yours = {f"- {t.name}: {t.prompt_snippet or t.description}" for t in tools}
    yours |= {f"- {g}" for t in tools for g in t.prompt_guidelines}

    lines = [("POST /chat/completions", None), ("{", None),
             (f'  "model": "{MODEL["id"]}",', BLUE), ('  "messages": [', None),
             ('    {"role": "system", "content":', BLUE)]
    system = session.system_prompt(tools).splitlines()
    for i, line in enumerate(system):
        shown = ('"' if i == 0 else " ") + line + ('"},' if i == len(system) - 1 else "")
        for j, part in enumerate(textwrap.wrap(shown, CHARS - 6) or [""]):
            lines.append(("      " + ("" if j == 0 else " ") + part, EXT1 if line in yours else BLUE))
    lines += [(f'    {{"role": "user", "content": "{PROMPT}"}}', YOU), ("  ],", None), ('  "tools": [', None)]

    for n, tool in enumerate(ai.convert_tools(tools)):
        f = tool["function"]
        last = "" if n == len(tools) - 1 else ","
        if n:  # one line for the others: the first one shows the whole shape
            lines.append((f'    {{"type": "function", "function": {{"name": "{f["name"]}", "description": …, "parameters": …}}}}{last}', EXT2))
            continue
        lines.append((f'    {{"type": "function", "function": {{"name": "{f["name"]}",', EXT2))
        for j, part in enumerate(textwrap.wrap(f'"description": {json.dumps(f["description"])},', CHARS - 6)):
            lines.append(("      " + ("  " if j else "") + part, EXT2))
        lines.append(('      "parameters": {"type": "object", "properties": {', EXT2))
        for name, prop in f["parameters"]["properties"].items():
            lines.append((f"        {json.dumps(name)}: {{\"type\": {json.dumps(prop['type'])}, \"description\": …}},", EXT2))
        lines.append((f'        }}, "required": {json.dumps(f["parameters"]["required"])}}}}}}}{last}', EXT2))
    lines += [("  ],", None), (f'  "max_tokens": {MODEL["max_tokens"]},', BLUE),
              ('  "stream": true, "stream_options": {"include_usage": true}', None), ("}", None)]
    return lines


def line_y(i):
    return TOP + 22 + i * LINE_H


def card(y, color, title, lines, mono=False):
    h = 40 + 19 * len(lines)
    out = [f'<rect x="{CARD_X}" y="{y}" width="{CARD_W}" height="{h}" rx="10" fill="{TINT[color]}" stroke="{color}" stroke-width="2"/>',
           text(CARD_X + 16, y + 25, title, size=15, color=color, weight="700")]
    for i, line in enumerate(lines):
        out.append(text(CARD_X + 16, y + 48 + 19 * i, line.replace(" ", " ") if mono else line,
                        size=12 if mono else 13, color="#1f2328", mono=mono))
    return out, h


def arrow(y1, y2, color, x_mid):
    return (f'<path d="M {CARD_X + CARD_W} {y1} H {x_mid} V {y2} H {PANEL_X - 4}" fill="none" stroke="{color}" '
            f'stroke-width="1.6" marker-end="url(#arrow-{color[1:]})"/>')


def main():
    lines = request_lines()
    parts = [heading(CARD_X, 40, "Where it comes from"), heading(PANEL_X, 40, "What the model receives, every turn")]
    panel_h = len(lines) * LINE_H + 20
    parts.append(f'<rect x="{PANEL_X}" y="{TOP}" width="{PANEL_W}" height="{panel_h}" rx="10" fill="#f6f8fa" stroke="#d1d5db"/>')
    for i, (line, color) in enumerate(lines):
        y = line_y(i)
        if color:
            parts.append(f'<rect x="{PANEL_X + 1}" y="{y - 14}" width="{PANEL_W - 2}" height="{LINE_H}" fill="{TINT[color]}"/>')
            parts.append(f'<rect x="{PANEL_X + 1}" y="{y - 14}" width="7" height="{LINE_H}" fill="{color}"/>')
        parts.append(text(PANEL_X + 18, y, line.replace(" ", " "), size=12.5,
                          color="#1f2328" if color else "#6b7280", mono=True))

    def rows(pred):
        found = [i for i, (line, color) in enumerate(lines) if pred(line, color)]
        return (line_y(found[0]) + line_y(found[-1])) / 2 - 4

    tools_at = next(i for i, (l, _) in enumerate(lines) if l.startswith('  "tools"'))
    targets = [
        (BLUE, "pi2", ["The system prompt around your tools,", "the model id and max_tokens."], False,
         [line_y(4) - 4]),
        (EXT1, "Your tools: in the system prompt", ['prompt_snippet="Read file contents"', 'prompt_guidelines=[...]'], True,
         [rows(lambda l, c: c == EXT1 and l.lstrip().startswith("- ") and ":" in l and lines.index((l, c)) < tools_at and "Use" not in l),
          rows(lambda l, c: c == EXT1 and l.lstrip().startswith("- Use ") and lines.index((l, c)) < tools_at)]),
        (YOU, "You", [PROMPT], False, [rows(lambda l, c: c == YOU)]),
        (EXT2, "Your tools: the tools entry", ['name="read"', 'description="Read the contents…"', 'parameters={...}'], True,
         [rows(lambda l, c: c == EXT2 and lines.index((l, c)) > tools_at)]),
    ]
    y = TOP
    for k, (color, title, body, mono, aims) in enumerate(targets):
        h = 40 + 19 * len(body)
        y = max(y, aims[0] - h / 2)
        card_parts, h = card(y, color, title, body, mono)
        parts += card_parts
        for m, aim in enumerate(aims):
            start = y + h / 2 + (m - (len(aims) - 1) / 2) * 16
            parts.append(arrow(start, aim, color, CARD_X + CARD_W + 22 + 8 * m))
        y += h + 18

    legend_y = TOP + panel_h + 28
    x = PANEL_X
    for color, label in [(BLUE, "pi2"), (YOU, "you"), (EXT1, "your tools: system prompt"), (EXT2, "your tools: tools entry")]:
        parts.append(f'<rect x="{x}" y="{legend_y - 12}" width="14" height="14" rx="3" fill="{TINT[color]}" stroke="{color}" stroke-width="2"/>')
        parts.append(text(x + 18, legend_y, label, size=13, color="#4b5563"))
        x += 36 + len(label) * 6.1
    y = max(legend_y + 22, y + 8)
    hint_parts, h = hint(y, ["The model sees only these lines, never your code: write name, description and parameters for it."])
    parts += hint_parts
    height = y + h + 20

    markers = "".join(
        f'<marker id="arrow-{c[1:]}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto">'
        f'<path d="M 0 0 L 10 5 L 0 10 z" fill="{c}"/></marker>' for c in (BLUE, YOU, EXT1, EXT2))
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height}" viewBox="0 0 {WIDTH} {height}" font-family="{SANS}" font-size="14">',
           f"<defs>{markers}</defs>", '<rect width="100%" height="100%" fill="#ffffff"/>', *parts, "</svg>"]
    OUT.write_text("\n".join(svg) + "\n")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
