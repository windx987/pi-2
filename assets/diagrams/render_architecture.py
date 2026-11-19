# Writes architecture.svg: the pi2 modules in request order, with what each one calls.
# Run from anywhere: python3 assets/diagrams/render_architecture.py
from pathlib import Path

OUT = Path(__file__).with_name("architecture.svg")
SANS = "-apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace"
WIDTH, HEIGHT = 1210, 758

# Columns: your code, start-up modules, the request path, what the request path uses.
COL = {"yours": (30, 190), "start": (310, 190), "main": (600, 250), "side": (950, 230)}
ROW = [118, 238, 358, 478, 598]
BOX_H = 74
STYLE = {
    "pi2": ("#eef3fa", "#2f5a96"),
    "yours": ("#fbeeee", "#b03a37"),
    "outside": ("#f3f4f6", "#6b7280"),
}


def esc(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def box(col, top, title, lines, kind="pi2", height=BOX_H, mono_title=True):
    x, w = COL[col]
    fill, stroke = STYLE[kind]
    family = MONO if mono_title else SANS
    out = [
        f'<rect x="{x}" y="{top}" width="{w}" height="{height}" rx="10" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>',
        f'<text x="{x + 14}" y="{top + 25}" fill="{stroke}" font-family="{family}" font-size="15" font-weight="700">{esc(title)}</text>',
    ]
    for i, line in enumerate(lines):
        mono = line.startswith("`")
        text = line.strip("`")
        family = MONO if mono else SANS
        out.append(f'<text x="{x + 14}" y="{top + 47 + i * 19}" fill="#374151" font-family="{family}" font-size="13">{esc(text)}</text>')
    return out


def mid(row):
    return ROW[row] + BOX_H / 2


def down(row, label, both=True):
    # Vertical arrow on the request path, from the box in `row` to the box below it.
    x = COL["main"][0] + COL["main"][1] / 2
    y1, y2 = ROW[row] + BOX_H, ROW[row + 1]
    start = ' marker-start="url(#arrow)"' if both else ""
    return [
        f'<line x1="{x}" y1="{y1 + 2}" x2="{x}" y2="{y2 - 2}" stroke="#6b7280" stroke-width="1.5" marker-end="url(#arrow)"{start}/>',
        f'<text x="{x + 10}" y="{(y1 + y2) / 2 + 5}" fill="#4b5563" font-size="12">{esc(label)}</text>',
    ]


def across(x1, x2, y, label, both=False, color="#6b7280", marker="arrow"):
    # Horizontal arrow from x1 to x2, label centred above it.
    start = f' marker-start="url(#{marker})"' if both else ""
    return [
        f'<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" stroke="{color}" stroke-width="1.5" marker-end="url(#{marker})"{start}/>',
        f'<text x="{(x1 + x2) / 2}" y="{y - 7}" text-anchor="middle" fill="#4b5563" font-size="12">{esc(label)}</text>',
    ]


def right(col):
    return COL[col][0] + COL[col][1]


def left(col):
    return COL[col][0]


parts = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" font-family="{SANS}" font-size="14">',
    "<defs>",
    '<marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#6b7280"/></marker>',
    '<marker id="arrowRed" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#b03a37"/></marker>',
    "</defs>",
    '<rect width="100%" height="100%" fill="#ffffff"/>',
]

# Column headings
for col, heading in [("yours", "Your code"), ("start", "At startup"), ("main", "Every request"), ("side", "Used on the way")]:
    parts.append(f'<text x="{left(col)}" y="{ROW[0] - 84}" fill="#4b5563" font-size="13" font-weight="700" letter-spacing="0.5">{heading.upper()}</text>')

# You
x, w = COL["main"]
parts += [
    f'<rect x="{x + 75}" y="{ROW[0] - 66}" width="100" height="30" rx="15" fill="#f3f4f6" stroke="#6b7280" stroke-width="1.5"/>',
    f'<text x="{x + w / 2}" y="{ROW[0] - 46}" text-anchor="middle" fill="#1f2328" font-weight="700">You</text>',
    f'<line x1="{x + w / 2}" y1="{ROW[0] - 34}" x2="{x + w / 2}" y2="{ROW[0] - 2}" stroke="#6b7280" stroke-width="1.5" marker-end="url(#arrow)" marker-start="url(#arrow)"/>',
]

# The request path
parts += box("main", ROW[0], "tui.py", ["InteractiveMode", "reads input, prints events"])
parts += down(0, "prompt() / events")
parts += box("main", ROW[1], "session.py", ["AgentSession", "history, tools, saving"])
parts += down(1, "run() / events")
parts += box("main", ROW[2], "agent_loop.py", ["`run, execute_tool_call", "ask the model, run its tools"])
parts += down(2, "stream_fn", both=False)
parts += box("main", ROW[3], "model_runtime.py", ["ModelRuntime", "model → provider, URL, key"])
parts += down(3, "stream()", both=False)
parts += box("main", ROW[4], "ai.py", ["`stream()", "OpenAI-compatible HTTP"])

# At startup
parts += box("start", ROW[0], "cli.py", ["`main()", "reads options, builds all"])
parts += across(right("start"), left("main"), mid(0), "starts")
parts += box("start", ROW[1], "extensions.py", ["ExtensionAPI", "`pi.tools, pi.handlers"])
x = left("start") + COL["start"][1] / 2
parts += [
    f'<line x1="{x}" y1="{ROW[0] + BOX_H + 2}" x2="{x}" y2="{ROW[1] - 2}" stroke="#6b7280" stroke-width="1.5" marker-end="url(#arrow)"/>',
    f'<text x="{x + 10}" y="{(ROW[0] + BOX_H + ROW[1]) / 2 + 5}" fill="#4b5563" font-size="12">load(path) per -e</text>',
]
parts += across(right("start"), left("main"), mid(1), "tools, handlers")

# Your code: loaded at startup, called for each tool call
top = ROW[1]
parts += box("yours", top, "Your extensions", ["`exercises/, examples/", "", "`def extension(pi):", "`\u00a0\u00a0register_tool(...)", "`\u00a0\u00a0on(\"tool_call\", h)", "", "loaded with -e"],
             kind="yours", height=ROW[2] + BOX_H - top, mono_title=False)
parts += across(right("yours"), left("start"), mid(1), "extension(pi)", color="#b03a37", marker="arrowRed")
parts += across(left("main"), right("yours"), mid(2), "execute(params, ctx) / result", both=True, color="#b03a37", marker="arrowRed")

# Used on the way
parts += box("side", ROW[1], "Session files", ["`~/.pi/agent/", "`python-sessions/*.jsonl"], kind="outside", mono_title=False)
parts += across(right("main"), left("side"), mid(1), "save()")
parts += box("side", ROW[2], "schema.py", ["`validate_tool_arguments", "checks them against the schema"])
parts += across(right("main"), left("side"), mid(2), "arguments")
parts += box("side", ROW[3], "Model list", ["`~/.pi/agent/", "`models.json"], kind="outside", mono_title=False)
parts += across(right("main"), left("side"), mid(3), "reads")
parts += box("side", ROW[4], "LLM server", ["e.g. Ollama /v1", "streams the answer"], kind="outside", mono_title=False)
parts += across(right("main"), left("side"), mid(4), "HTTP", both=True)

# Legend
y = HEIGHT - 30
for i, (kind, label) in enumerate([("pi2", "module in pi2/"), ("yours", "your code"), ("outside", "outside pi2")]):
    fill, stroke = STYLE[kind]
    lx = 30 + i * 190
    parts.append(f'<rect x="{lx}" y="{y - 13}" width="22" height="16" rx="4" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>')
    parts.append(f'<text x="{lx + 30}" y="{y}" fill="#4b5563" font-size="13">{label}</text>')

parts.append("</svg>")
OUT.write_text("\n".join(parts) + "\n")
print(f"wrote {OUT}")
