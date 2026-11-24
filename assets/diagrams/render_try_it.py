# Writes exercise-NN-try.svg for each exercise and playground-3-context.svg, playground-4-gate.svg: one row
# per thing you ask, with the tool calls the agent should make and what you should see, and a hint.
# Run from anywhere: python3 assets/diagrams/render_try_it.py
import textwrap

from render_playground import BLUE, GRAY, GREEN, PURPLE, RED, THRESHOLD, TINT, TOOL, WIDTH, WINDOW, esc, heading, hint, text, write

MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace"
ASK_X, ASK_W = 30, 330
CALL_X, CALL_W = 390, 330
SEE_X, SEE_W = 750, 320
# A call ends green (its result), red (an error result), or grey: blocked before it ran, or still working.
STATUS = {"ok": (GREEN, "✓"), "error": (RED, "✗"), "blocked": (GRAY, "⊘"), "auto": (PURPLE, "↻")}


def ask_bubble(y, ask):
    """What you type: a message in a bubble, or a /command in monospace."""
    command = ask.startswith("/")
    lines = textwrap.wrap(ask, 30 if command else 44)
    h = 16 + 18 * len(lines)
    out = [f'<rect x="{ASK_X}" y="{y}" width="{ASK_W}" height="{h}" rx="10" fill="{TINT[BLUE]}" stroke="{BLUE}" stroke-width="1.2"/>']
    for i, line in enumerate(lines):
        if command:
            out.append(f'<text x="{ASK_X + 14}" y="{y + 22 + 18 * i}" fill="{BLUE}" font-size="13" font-weight="700" font-family="{MONO}">{esc(line)}</text>')
        else:
            out.append(text(ASK_X + 14, y + 22 + 18 * i, line, size=13, color="#1a2b45"))
    return out, h


def call_chip(y, tool, label, status):
    """One tool call: the tool's badge, its argument, and how it ended."""
    color, mark = STATUS[status]
    badge = TOOL.get(tool, GRAY) if tool != "compaction" else PURPLE
    bw = len(tool) * 7.4 + 16
    out = [
        f'<rect x="{CALL_X}" y="{y}" width="{CALL_W}" height="26" rx="7" fill="{TINT[color]}" stroke="{color}" stroke-width="1.2"/>',
        f'<rect x="{CALL_X + 5}" y="{y + 4}" width="{bw}" height="18" rx="9" fill="{badge}"/>',
        f'<text x="{CALL_X + 5 + bw / 2}" y="{y + 17}" fill="#fff" font-size="11" font-weight="700" text-anchor="middle" font-family="{MONO}">{esc(tool)}</text>',
        f'<text x="{CALL_X + bw + 13}" y="{y + 17.5}" fill="#1f2328" font-size="12" font-family="{MONO}">{esc(label[:40 - len(tool)])}</text>',
        f'<text x="{CALL_X + CALL_W - 12}" y="{y + 18}" fill="{color}" font-size="14" font-weight="700" text-anchor="end">{mark}</text>',
    ]
    return out, 32


def mini_bar(x, y, w, tokens):
    """The context window as a thin bar, filled up to tokens, with the compaction mark."""
    t = x + w * THRESHOLD / WINDOW
    fill = RED if tokens > THRESHOLD else GREEN
    return [
        f'<rect x="{x}" y="{y}" width="{w}" height="8" rx="4" fill="#f3f4f6" stroke="#d1d5db"/>',
        f'<rect x="{x}" y="{y}" width="{max(4, w * min(tokens, WINDOW) / WINDOW)}" height="8" rx="4" fill="{fill}" opacity="0.8"/>',
        f'<line x1="{t}" y1="{y - 4}" x2="{t}" y2="{y + 12}" stroke="#1f2328" stroke-width="1" stroke-dasharray="2 2"/>',
    ]


def figure(name, rows, hint_lines, note=None):
    """rows: (ask, [(tool, label, status), ...], what you should see, context tokens or None)."""
    parts = [heading(ASK_X, 28, "You ask"), heading(CALL_X, 28, "The agent calls"), heading(SEE_X, 28, "You should see")]
    y = 44
    for ask, calls, see, tokens in rows:
        bubble, bh = ask_bubble(y, ask)
        chips, ch = [], 0
        for tool, label, status in calls:
            chip, h = call_chip(y + ch, tool, label, status)
            chips += chip
            ch += h
        if not calls:
            chips.append(text(CALL_X + 4, y + 22, "no tool call: a pi2 command", size=12, color="#6b7280"))
            ch = 30
        lines = textwrap.wrap(see, 46)
        see_parts = [text(SEE_X, y + 18 + 18 * i, line, size=13, color="#374151") for i, line in enumerate(lines)]
        sh = 10 + 18 * len(lines)
        if tokens is not None:
            see_parts += mini_bar(SEE_X, y + sh + 2, SEE_W - 10, tokens)
            sh += 18
        h = max(bh, ch, sh)
        arrow_y = y + 16
        parts += bubble + chips + see_parts
        parts.append(f'<line x1="{ASK_X + ASK_W + 6}" y1="{arrow_y}" x2="{CALL_X - 6}" y2="{arrow_y}" stroke="#9ca3af" stroke-width="1.4" marker-end="url(#arrow)"/>')
        parts.append(f'<line x1="{CALL_X + CALL_W + 6}" y1="{arrow_y}" x2="{SEE_X - 8}" y2="{arrow_y}" stroke="#9ca3af" stroke-width="1.4" marker-end="url(#arrow)"/>')
        y += h + 14
        parts.append(f'<line x1="30" y1="{y - 7}" x2="{WIDTH - 30}" y2="{y - 7}" stroke="#eef0f3"/>')
    if note:
        parts.append(text(30, y + 10, note, size=12, color="#4b5563"))
        y += 22
    h_parts, h = hint(y + 6, hint_lines)
    write(name, y + 6 + h + 20, parts + h_parts)


def exercises():
    figure("exercise-01-try.svg", [
        ("What does calc.py define?", [("read", "calc.py", "ok")], "The first lines of calc.py in the box, then an answer naming add and average.", None),
        ("Show me lines 8 to 10 of calc.py.", [("read", "calc.py:8-10", "ok")],
         "Three lines and your note: [2 more lines. Use offset=11 to continue.]", None),
        ("Read missing.txt.", [("read", "missing.txt", "error")],
         "A red box with your message. The agent says the file does not exist instead of inventing it.", None),
    ], ["With only read, the agent cannot list a folder: it may first try \"read .\" and get an error. That is fine; name the "
        "file in your question and it reads it."])
    figure("exercise-02-try.svg", [
        ("Create notes/todo.md with three workshop goals, then read it back.",
         [("write", "notes/todo.md", "ok"), ("read", "notes/todo.md", "ok")],
         "Wrote N bytes to notes/todo.md, then its content. cat notes/todo.md shows the same.", None),
        ("Write a file to /tmp/outside.txt.", [("write", "/tmp/outside.txt", "error")],
         "Refusing to write outside the working directory. The file does not exist; the agent explains.", None),
    ], ["The model does not see the file it wrote unless it reads it: your short confirmation is all it gets, so say what "
        "happened and where."])
    figure("exercise-03-try.svg", [
        ("Run the tests.", [("bash", "python3 -m unittest", "error")], "The test output with one failing test, and exit code 1: a red result the model reads.", None),
        ("Why does the test fail?", [("read", "calc.py", "ok"), ("read", "test_calc.py", "ok")],
         "The agent explains: average() divides by len(values) - 1. Fixing it is exercise 04.", None),
        ("Run sleep 30 with a 2 second timeout.", [("bash", "sleep 30  timeout 2", "error")],
         "Command stopped after 2 seconds. ps in another terminal shows no sleep 30 left.", None),
        ("Delete the incidents folder with rm -rf.", [("bash", "rm -rf incidents", "blocked")],
         "Blocked by the permission gate before it runs; the folder stays.", None),
    ], ["The commands run on your machine, as you: keep examples/permission_gate.py loaded and run from the repository root "
        "with --cwd playground. ctrl+c stops a running command."])
    figure("exercise-04-try.svg", [
        ("Fix the failing test.", [("bash", "python3 -m unittest", "error"), ("read", "calc.py", "ok"), ("edit", "calc.py", "ok"), ("bash", "python3 -m unittest", "ok")],
         "All four tools in one task: the edit changes one line of average(), and the tests pass.", None),
        ("Rename add to plus in calc.py and update its callers.", [("edit", "calc.py  2 edits", "ok"), ("edit", "test_calc.py", "ok")],
         "Two replacements in calc.py, and the import in test_calc.py, each with its diff. grep -n plus *.py shows them.", None),
        ("In calc.py, replace return a + b with return a - b  (after you copied that line once more)",
         [("edit", "calc.py", "error"), ("read", "calc.py", "ok"), ("edit", "calc.py", "ok")],
         "edits[0] occurs 2 times: refused. The agent reads the file and retries with more context, or asks you which one.", None),
    ], ["Each oldText must occur exactly once in the original file. If the playground is already fixed, reset it "
        "first: git restore playground && git clean -fd playground"])
    figure("exercise-05-try.svg", [
        ("The reports in incidents/ are INC-2601.md to INC-2630.md. Use three subagents … one line per report … numbered.",
         [("subagent", "INC-2601 … INC-2610", "ok"), ("subagent", "INC-2611 … INC-2620", "ok"), ("subagent", "INC-2621 … INC-2630", "ok")],
         "Each box grey while its subagent reads 10 reports, then green with 10 yes or no lines and your cost note. "
         "Then the yes lines, numbered.", 3000),
        ("/context", [], "Only the three lists are in the parent's context: a few thousand tokens, far from the mark.", 3000),
    ], ["Give a subagent a complete task: its files, what to look for, what to return; it sees nothing of your "
        "conversation. Expect a few minutes: one request per report, one subagent after another."],
       note="The full ask is in the README. The bar is the parent's context; the dashed mark is where compaction starts (16k of 32k).")


def playground():
    figure("playground-3-context.svg", [
        ("/context", [], "The system prompt and one tool: under 1k of 33k.", 700),
        ("Read INC-2601.md to INC-2608.md in incidents/ and give one line per report …",
         [("read", "incidents/INC-2601.md", "ok"), ("read", "…  8 reads or more", "ok")], "One yes or no line per report.", 9000),
        ("/context", [], "Tool results are most of it, 7k to 10k: a small model sometimes reads a file twice.", 9000),
        ("/compact keep the yes or no line of every report", [],
         "Compacted N messages, with the tokens before and after, and the start of the summary. The newest 4k stay word for word.", 5000),
        ("Read INC-2609.md to INC-2630.md the same way.",
         [("read", "…  reads", "ok"), ("compaction", "context passed 16k", "auto"), ("read", "…  reads", "ok")],
         "Context is filling up: summarizing older messages..., another Compacted box, and the agent reads on.", 14000),
        ("/new", [], "New session started, and the context is empty again. Ask what it found: it does not know, and reads the reports again.", 700),
    ], ["The parts in /context are estimates, scaled to the model's last count. A summary keeps what it is asked to keep: "
        "say it in /compact's focus. Compare the final yes lines with scenario 2, where the parent never held the reports."],
       note="The bars show the context after each step; the dashed mark is where automatic compaction starts (16k of 32k).")
    figure("playground-4-gate.svg", [
        ("Delete the incidents folder with rm -rf.", [("bash", "rm -rf incidents", "blocked")],
         "Blocked by extension: Dangerous command blocked … Ask the user to run it themselves. The folder is still there.", None),
        ("Run sudo ls.", [("bash", "sudo ls", "blocked")], "Blocked as well: the gate matches sudo.", None),
        ("List the files in incidents/.", [("bash", "ls incidents", "ok")], "Runs: the gate lets every other command through.", None),
    ], ["The gate reads the text of the command, before it runs. It is a way to ask first, not a wall: "
        "\"find incidents -delete\" gets through. Nothing else isolates the commands: read each one the agent runs."],
       note="⊘ blocked before it ran: the tool's execute() never runs, and the model gets the reason as an error result.")


exercises()
playground()
