# Writes playground-1-test.svg and playground-2-incidents.svg: for each playground
# scenario, what the agent does with which tool, how much of the context it needs, and a hint.
# Run from anywhere: python3 assets/diagrams/render_playground.py
import textwrap
from pathlib import Path

HERE = Path(__file__).parent
SANS = "-apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace"
WIDTH = 1100
WINDOW = 32768
THRESHOLD = 16384
# Tool colors: the agent's own tools red (you build them), the subagent purple.
TOOL = {"read": "#b03a37", "write": "#b03a37", "bash": "#b03a37", "edit": "#b03a37", "subagent": "#6d4bb3"}
BLUE, GREEN, RED, PURPLE, AMBER, GRAY = "#2f5a96", "#2f7d5b", "#b03a37", "#6d4bb3", "#b7791f", "#6b7280"
TINT = {BLUE: "#eef3fa", GREEN: "#edf7f2", RED: "#fbeeee", PURPLE: "#f3effa", AMBER: "#fdf6e7", GRAY: "#f3f4f6"}


def esc(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def heading(x, y, text):
    return f'<text x="{x}" y="{y}" fill="#4b5563" font-size="12" font-weight="700" letter-spacing="0.5">{esc(text.upper())}</text>'


def text(x, y, value, size=13, color="#374151", mono=False, weight="400", anchor="start"):
    family = f' font-family="{MONO}"' if mono else ""
    return (f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" font-weight="{weight}" text-anchor="{anchor}"{family}>'
            f"{esc(value)}</text>")


def flow(y, steps):
    """Steps left to right: a box with a tool badge, a title and a line, joined by arrows."""
    out, gap = [], 26
    w = (WIDTH - 60 - gap * (len(steps) - 1)) / len(steps)
    for i, (tool, title, line) in enumerate(steps):
        x = 30 + i * (w + gap)
        color = TOOL.get(tool, BLUE)
        out.append(f'<rect x="{x}" y="{y}" width="{w}" height="84" rx="10" fill="{TINT[color]}" stroke="{color}" stroke-width="1.5"/>')
        if tool:
            bw = len(tool) * 8 + 16
            out.append(f'<rect x="{x + 12}" y="{y + 12}" width="{bw}" height="20" rx="10" fill="{color}"/>')
            out.append(text(x + 12 + bw / 2, y + 26, tool, size=12, color="#fff", mono=True, weight="700", anchor="middle"))
        out.append(text(x + 12, y + 53, title, size=14, color="#1f2328", weight="700"))
        out.append(text(x + 12, y + 72, line, size=12, color="#4b5563"))
        if i:
            out.append(f'<line x1="{x - gap + 3}" y1="{y + 42}" x2="{x - 3}" y2="{y + 42}" stroke="#6b7280" stroke-width="1.5" marker-end="url(#arrow)"/>')
    return out


def context_bar(x, y, w, label, tokens, note):
    """The context window as a track, the context in it, and the compaction threshold."""
    used = min(tokens, WINDOW)
    color = RED if tokens > THRESHOLD else GREEN
    t = x + w * THRESHOLD / WINDOW
    out = [
        text(x, y - 8, label, size=13, color="#1f2328", weight="600"),
        f'<rect x="{x}" y="{y}" width="{w}" height="12" rx="6" fill="#f3f4f6" stroke="#d1d5db"/>',
        f'<rect x="{x}" y="{y}" width="{max(6, w * used / WINDOW)}" height="12" rx="6" fill="{color}" opacity="0.8"/>',
        f'<line x1="{t}" y1="{y - 5}" x2="{t}" y2="{y + 17}" stroke="#1f2328" stroke-width="1.2" stroke-dasharray="3 3"/>',
        text(x, y + 30, note, size=12, color=color if tokens > THRESHOLD else "#4b5563"),
    ]
    if tokens > WINDOW:  # spills over the end of the window
        out.append(f'<path d="M {x + w + 4} {y} l 10 6 l -10 6 z" fill="{RED}"/>')
    return out


def hint(y, lines):
    body = [line for paragraph in lines for line in textwrap.wrap(paragraph, 148)]
    h = 22 + len(body) * 20
    out = [
        f'<rect x="30" y="{y}" width="{WIDTH - 60}" height="{h}" rx="10" fill="{TINT[AMBER]}" stroke="{AMBER}" stroke-width="1.5"/>',
        f'<text x="48" y="{y + 26}" fill="{AMBER}" font-size="12" font-weight="700" letter-spacing="0.6">HINT</text>',
    ]
    out += [text(96, y + 26 + i * 20, line, size=13, color="#4a3510") for i, line in enumerate(body)]
    return out, h


def write(name, height, parts):
    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height}" viewBox="0 0 {WIDTH} {height}" font-family="{SANS}" font-size="14">',
        '<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#6b7280"/></marker></defs>',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        *parts,
        "</svg>",
    ]
    (HERE / name).write_text("\n".join(svg) + "\n")
    print(f"wrote {HERE / name}")


def scenario_test():
    parts = [heading(30, 28, "What the agent does")]
    parts += flow(42, [
        ("bash", "Run the tests", "python3 -m unittest: 1 failing"),
        ("read", "Read the code", "calc.py and test_calc.py"),
        ("edit", "Fix the bug", "one line in average()"),
        ("bash", "Run them again", "python3 -m unittest: OK"),
    ])
    parts.append(heading(30, 168, "The project"))
    code = ["def average(values):", "    total = 0", "    for value in values:", "        total = add(total, value)",
            "    return total / (len(values) - 1)"]
    parts.append(f'<rect x="30" y="180" width="520" height="118" rx="8" fill="#f6f8fa" stroke="#d1d5db"/>')
    # Non-breaking spaces: SVG would collapse the indentation.
    parts += [text(46, 204 + i * 20, line.replace(" ", "\u00a0"), size=13, mono=True, color="#1f2328") for i, line in enumerate(code)]
    parts.append(text(566, 204, "calc.py: two small functions", size=13))
    parts.append(text(566, 226, "test_calc.py: two tests, one fails", size=13))
    parts.append(text(566, 248, "Small enough to read whole:", size=13))
    parts += context_bar(566, 272, 500, "", 1500, "the whole task uses a few thousand tokens")
    h_parts, h = hint(322, [
        "Ask for the goal, not the steps: \"Run the tests and fix what fails.\" The agent picks the tools itself. "
        "Read the bug line yourself first: which number should the sum be divided by? If the agent edits without running "
        "the tests again, ask it to check.",
    ])
    write("playground-1-test.svg", 322 + h + 20, parts + h_parts)


def scenario_incidents():
    parts = [heading(30, 28, "What the agent does")]
    parts += flow(42, [
        ("subagent", "Split the work", "three tasks of 10 reports"),
        ("read", "Each reads 10", "in its own, empty context"),
        ("", "Each answers", "a short list: number, date, cause"),
        ("", "Parent combines", "three lists into one answer"),
    ])
    parts.append(heading(30, 168, "30 reports, about 25k tokens"))
    for g in range(3):
        gx = 30 + g * 172
        parts.append(f'<rect x="{gx}" y="180" width="160" height="96" rx="8" fill="{TINT[PURPLE]}" stroke="{PURPLE}" stroke-width="1.2"/>')
        for i in range(10):
            x, y = gx + 12 + (i % 5) * 28, 192 + (i // 5) * 30
            parts.append(f'<path d="M {x} {y} h 16 l 6 6 v 18 h -22 z" fill="#ffffff" stroke="{GRAY}" stroke-width="1"/>')
        parts.append(text(gx + 80, 268, f"subagent {g + 1}: INC-{2601 + g * 10}–{2610 + g * 10}", size=11, color=PURPLE, anchor="middle"))
        parts.append(f'<line x1="{gx + 80}" y1="278" x2="{270}" y2="318" stroke="{PURPLE}" stroke-width="1.2" marker-end="url(#arrow)"/>')
    parts.append(f'<rect x="200" y="320" width="140" height="34" rx="8" fill="{TINT[BLUE]}" stroke="{BLUE}" stroke-width="1.5"/>')
    parts.append(text(270, 342, "parent: 3 lists", size=13, color=BLUE, weight="700", anchor="middle"))
    parts += context_bar(566, 210, 500, "Parent reads all 30 itself", 25000 + 3000, "about 25k tokens: compacts, early findings may be lost")
    parts += context_bar(566, 288, 500, "Parent with three subagents", 2500, "only the three lists; each subagent holds about 9k")
    parts.append(text(566, 350, "The dashed line is where compaction starts (16k of 32k).", size=12, color="#4b5563"))
    h_parts, h = hint(380, [
        "A subagent sees nothing of your conversation: give each one a complete task, with its files (INC-2601 to INC-2610), what "
        "to look for, and what to return. The root cause is in the last section of each report. Careful: some logs are full of "
        "database timeouts although the database was fine, so read the cause, not the logs. Expect a few minutes: one request "
        "per report, and each subagent box stays grey until its subagent answers.",
    ])
    write("playground-2-incidents.svg", 380 + h + 20, parts + h_parts)


if __name__ == "__main__":
    scenario_test()
    scenario_incidents()
