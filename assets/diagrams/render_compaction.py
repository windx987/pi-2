# Writes compaction.svg: what the model sees before and after a compaction, against the context window.
# Run from anywhere: python3 assets/diagrams/render_compaction.py
from pathlib import Path

OUT = Path(__file__).with_name("compaction.svg")
SANS = "-apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace"
WIDTH, HEIGHT = 1210, 610
LEFT, RIGHT = 30, 1180
WINDOW = 32768  # the workshop model; one pixel per WINDOW / (RIGHT - LEFT) tokens
THRESHOLD = WINDOW - 16384
KEEP = 8192
STYLE = {
    "system": ("#f3f4f6", "#6b7280"),
    "user": ("#eef3fa", "#2f5a96"),
    "assistant": ("#f3effa", "#6d4bb3"),
    "tool": ("#edf7f2", "#2f7d5b"),
    "summary": ("#fdf6e7", "#b7791f"),
}
LABEL = {"system": "system", "user": "user", "assistant": "answer", "tool": "tool result", "summary": "summary"}

# (kind, tokens): a session that read a few files, then asked for a fix.
BEFORE = [("system", 900), ("user", 300), ("assistant", 500), ("tool", 4200), ("assistant", 400), ("tool", 3800),
          ("assistant", 600), ("user", 200), ("assistant", 500), ("tool", 2600), ("assistant", 700), ("tool", 4000)]
SUMMARY = 1300


def esc(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def x_of(tokens):
    return LEFT + tokens * (RIGHT - LEFT) / WINDOW


def heading(y, text):
    return f'<text x="{LEFT}" y="{y}" fill="#4b5563" font-size="13" font-weight="700" letter-spacing="0.5">{text.upper()}</text>'


def strip(y, messages, faded=0):
    """One block per message, as wide as its tokens. The first `faded` messages are drawn dimmed."""
    out, tokens = [], 0
    for i, (kind, n) in enumerate(messages):
        fill, stroke = STYLE[kind]
        x, w = x_of(tokens), n * (RIGHT - LEFT) / WINDOW
        opacity = ' opacity="0.45"' if 0 < i < faded else ""
        out.append(f'<rect x="{x + 1}" y="{y}" width="{w - 2}" height="46" rx="6" fill="{fill}" stroke="{stroke}" stroke-width="1.5"{opacity}/>')
        if w > 64:
            out.append(f'<text x="{x + w / 2}" y="{y + 28}" text-anchor="middle" fill="{stroke}" font-size="12" font-weight="600"{opacity}>{LABEL[kind]}</text>')
        tokens += n
    return out, tokens


def window_bar(y, used):
    """The context window as a track, the context in it, and the threshold where compaction starts."""
    t = x_of(THRESHOLD)
    color = "#b03a37" if used > THRESHOLD else "#2f7d5b"
    return [
        f'<rect x="{LEFT}" y="{y}" width="{RIGHT - LEFT}" height="12" rx="6" fill="#f3f4f6" stroke="#d1d5db"/>',
        f'<rect x="{LEFT}" y="{y}" width="{x_of(used) - LEFT}" height="12" rx="6" fill="{color}" opacity="0.8"/>',
        f'<line x1="{t}" y1="{y - 8}" x2="{t}" y2="{y + 20}" stroke="#1f2328" stroke-width="1.5" stroke-dasharray="4 3"/>',
        f'<text x="{LEFT}" y="{y + 34}" fill="#4b5563" font-size="12">context: about {used / 1000:.0f}k tokens</text>',
        f'<text x="{t + 8}" y="{y + 34}" fill="#1f2328" font-size="12">contextWindow - reserveTokens = 16k</text>',
        f'<text x="{RIGHT}" y="{y + 34}" text-anchor="end" fill="#4b5563" font-size="12">contextWindow = 32k</text>',
    ]


def brace(x1, x2, y, label, color):
    return [
        f'<path d="M {x1 + 2} {y} v 8 H {x2 - 2} v -8" fill="none" stroke="{color}" stroke-width="1.5"/>',
        f'<text x="{(x1 + x2) / 2}" y="{y + 26}" text-anchor="middle" fill="{color}" font-size="13" font-weight="600">{esc(label)}</text>',
    ]


parts = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" font-family="{SANS}" font-size="14">',
    '<rect width="100%" height="100%" fill="#ffffff"/>',
]

# Before: over the threshold. The cut keeps about KEEP tokens from the end, never a tool result alone.
parts.append(heading(32, "Before: the next request would be over the threshold"))
blocks, used = strip(50, BEFORE)
parts += blocks
cut, total = len(BEFORE), 0
for i in range(len(BEFORE) - 1, 0, -1):
    total += BEFORE[i][1]
    if total >= KEEP:
        cut = i
        while BEFORE[cut][0] == "tool":
            cut -= 1
        break
cut_x = x_of(sum(n for _, n in BEFORE[:cut]))
parts += brace(x_of(BEFORE[0][1]), cut_x, 104, "older messages: summarized", "#b7791f")
parts += brace(cut_x, x_of(used), 104, "newest messages: kept word for word (keepRecentTokens)", "#2f5a96")
parts += window_bar(166, used)

# The step between: one request to the model, without tools.
mid = 268
parts += [
    f'<line x1="{WIDTH / 2}" y1="{mid - 40}" x2="{WIDTH / 2}" y2="{mid + 52}" stroke="#6b7280" stroke-width="1.5" marker-end="url(#arrow)"/>',
    f'<rect x="{WIDTH / 2 + 20}" y="{mid - 26}" width="520" height="62" rx="10" fill="#eef3fa" stroke="#2f5a96" stroke-width="1.5"/>',
    f'<text x="{WIDTH / 2 + 34}" y="{mid - 3}" fill="#2f5a96" font-family="{MONO}" font-size="14" font-weight="700">compaction.summarize()</text>',
    f'<text x="{WIDTH / 2 + 34}" y="{mid + 20}" fill="#374151" font-size="13">the older messages as text → the model → goal, progress, next steps</text>',
    '<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#6b7280"/></marker></defs>',
]

# After: the system prompt, the summary, the kept messages.
after = [BEFORE[0], ("summary", SUMMARY), *BEFORE[cut:]]
parts.append(heading(352, "After: what the model sees from now on"))
blocks, used_after = strip(370, after)
parts += blocks
parts += brace(x_of(BEFORE[0][1]), x_of(BEFORE[0][1] + SUMMARY), 424, "summary", "#b7791f")
parts += window_bar(486, used_after)

# Legend
y = HEIGHT - 22
lx = LEFT
for kind in ("system", "user", "assistant", "tool", "summary"):
    fill, stroke = STYLE[kind]
    label = {"assistant": "model's answer"}.get(kind, LABEL[kind])
    parts.append(f'<rect x="{lx}" y="{y - 13}" width="22" height="16" rx="4" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>')
    parts.append(f'<text x="{lx + 30}" y="{y}" fill="#4b5563" font-size="13">{label}</text>')
    lx += 30 + len(label) * 7.4 + 34
parts.append(f'<text x="{RIGHT}" y="{y}" text-anchor="end" fill="#4b5563" font-size="13">The session file keeps every message.</text>')

parts.append("</svg>")
OUT.write_text("\n".join(parts) + "\n")
print(f"wrote {OUT}")
