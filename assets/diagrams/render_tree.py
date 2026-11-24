# Renders <name>.txt to <name>.svg: a file tree with an aligned explanation column, rows grouped into
# tinted sections. Usage: python3 render_tree.py [name], default python-structure.
import math
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
# The colors of Pi's packages: coding-agent blue, agent purple, ai green, your code red.
COLORS = {
    "d": {"path": "#1a2b45", "note": "#1a2b45"},
    "a": {"path": "#2f5a96", "note": "#1a2b45"},
    "l": {"path": "#6d4bb3", "note": "#1a2b45"},
    "m": {"path": "#2f7d5b", "note": "#1a2b45"},
    "w": {"path": "#b03a37", "note": "#4a1a18"},
    "r": {"path": "#b7791f", "note": "#4a3510"},
    "o": {"path": "#6b7280", "note": "#6b7280"},
}
LEGEND = [
    ("a", "app: terminal, session, models"),
    ("l", "agent loop"),
    ("m", "talks to the model"),
    ("w", "where you work"),
    ("r", "read and run"),
    ("o", "outside the workshop"),
]
# Section bands: a tint and a label color, chosen by the first role in the section.
BANDS = {
    "a": {"fill": "#f4f7fc", "label": "#2f5a96"},
    "w": {"fill": "#fcf3f3", "label": "#b03a37"},
    "r": {"fill": "#fcf7ec", "label": "#b7791f"},
    "o": {"fill": "#f6f7f8", "label": "#6b7280"},
}

FONT_SIZE = 14
CHAR_WIDTH = 9.1  # advance of a 14px monospace glyph, with room for wider fonts such as Menlo
LINE_HEIGHT = 24
PAD = 24
LABEL_SIZE = 11


def num(value):
    """A number as JavaScript prints it: 24, not 24.0."""
    return str(int(value)) if float(value).is_integer() else repr(value)


def escape(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render(name):
    rows, labels, section = [], [], None
    for line in (HERE / f"{name}.txt").read_text(encoding="utf-8").split("\n"):
        if line.startswith("## "):
            section = line[3:]
            labels.append(section)
            continue
        if not line or line.startswith("#"):
            continue
        path, _, note = line[2:].partition(" -- ")
        rows.append({"role": line[0], "path": path, "note": note, "section": section})

    note_x = PAD + max(len(row["path"]) for row in rows) * CHAR_WIDTH + 32
    notes_end = note_x + max(len(row["note"]) for row in rows) * CHAR_WIDTH
    labels = [label for label in labels if any(row["section"] == label for row in rows)]
    label_width = max([0] + [len(label) * 7.4 for label in labels]) + 24

    def legend_item_width(item):
        return 18 + len(item[1]) * CHAR_WIDTH + 28

    legend_rows = [LEGEND[:3], LEGEND[3:]]
    legend_width = max(sum(legend_item_width(item) for item in items) - 28 for items in legend_rows)
    width = math.ceil(max(notes_end + 24 + label_width, PAD + legend_width) + PAD)
    legend_y = PAD + len(rows) * LINE_HEIGHT + 22
    height = legend_y + len(legend_rows) * 24 + PAD

    # Section bands behind their rows, with the label at the right.
    band_shapes = []
    for label in labels:
        members = [i for i, row in enumerate(rows) if row["section"] == label]
        top = PAD + members[0] * LINE_HEIGHT + 3
        h = len(members) * LINE_HEIGHT - 3  # a small gap between neighbouring bands
        band = BANDS.get(rows[members[0]]["role"], BANDS["o"])
        band_shapes.append(
            f'<rect x="{num(PAD - 10)}" y="{num(top)}" width="{num(width - 2 * PAD + 20)}" height="{num(h)}" rx="8" fill="{band["fill"]}"/>'
            f'<text x="{num(width - PAD)}" y="{num(top + 17)}" text-anchor="end" fill="{band["label"]}" '
            f"font-family=\"-apple-system, 'Segoe UI', Helvetica, Arial, sans-serif\" font-size=\"{LABEL_SIZE}\" "
            f'font-weight="700" letter-spacing="0.6">{escape(label.upper())}</text>'
        )

    lines = []
    for i, row in enumerate(rows):
        y = PAD + (i + 1) * LINE_HEIGHT - 6
        branch = re.match(r"^[│├└─\s]*", row["path"]).group(0)
        name_part = row["path"][len(branch):]
        color = COLORS[row["role"]]
        # One text run, so the browser places the name right after the branch glyphs.
        out = (f'<text x="{num(PAD)}" y="{num(y)}"><tspan fill="#9aa7b8">{escape(branch)}</tspan>'
               f'<tspan fill="{color["path"]}" font-weight="600">{escape(name_part)}</tspan></text>')
        if row["note"]:
            out += f'<text x="{num(note_x)}" y="{num(y)}" fill="{color["note"]}">{escape(row["note"])}</text>'
        lines.append(out)

    legend_items = []
    for r, items in enumerate(legend_rows):
        x, y = PAD, legend_y + r * 24
        for item in items:
            role, label = item
            legend_items.append(
                f'<rect x="{num(x)}" y="{num(y)}" width="12" height="12" rx="2" fill="{COLORS[role]["path"]}"/>'
                f'<text x="{num(x + 18)}" y="{num(y + 11)}" fill="#4b5563">{escape(label)}</text>'
            )
            x += legend_item_width(item)

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" xml:space="preserve" width="{width}" height="{num(height)}" '
        f'viewBox="0 0 {width} {num(height)}" '
        f"font-family=\"ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace\" font-size=\"{FONT_SIZE}\">\n"
        '<rect width="100%" height="100%" fill="#ffffff"/>\n'
        + "\n".join(band_shapes) + "\n"
        + "\n".join(lines) + "\n"
        + f'<line x1="{num(PAD)}" y1="{num(legend_y - 12)}" x2="{num(width - PAD)}" y2="{num(legend_y - 12)}" stroke="#e5e7eb"/>\n'
        + "\n".join(legend_items) + "\n"
        + "</svg>\n"
    )
    (HERE / f"{name}.svg").write_text(svg, encoding="utf-8")
    print(f"wrote {HERE / f'{name}.svg'}")


if __name__ == "__main__":
    render(sys.argv[1] if len(sys.argv) > 1 else "python-structure")
