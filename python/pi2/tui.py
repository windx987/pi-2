"""Step 1: interactive mode, the terminal app.

Waits for your input between two border lines, hands it to the session, and renders every event the
session emits while the answer streams in: thinking, text, and tool calls in colored boxes. The layout
and colors follow Pi's interactive mode and dark theme, drawn with plain ANSI escape codes.
"""

import os
import shutil
import sys
import textwrap
from contextlib import contextmanager

try:
    import readline  # noqa: F401  (line editing and history for input())
    import termios
except ImportError:  # Windows
    termios = None

from . import __version__

RESET = "\x1b[0m"
BOLD = "\x1b[1m"
DIM = "\x1b[2m"
ITALIC = "\x1b[3m"


def fg(r, g, b):
    return f"\x1b[38;2;{r};{g};{b}m"


def bg(r, g, b):
    return f"\x1b[48;2;{r};{g};{b}m"


# Pi's logo colors; the rest approximates Pi's dark theme.
CORAL, BLUE, YELLOW, MINT = (228, 138, 122), (79, 142, 179), (234, 182, 93), (121, 191, 163)
ACCENT = fg(198, 146, 234)
WARNING = fg(222, 199, 101)
ERROR = fg(240, 137, 110)
MUTED = fg(160, 165, 178)
USER_BG = bg(43, 50, 82)
TOOL_BG = {"pending": bg(52, 54, 60), "success": bg(30, 70, 55), "error": bg(88, 48, 40)}
PREVIEW_LINES = 5


@contextmanager
def no_echo():
    """Hide what is typed while the agent works. The keys stay buffered and appear in the next editor."""
    if termios is None:
        yield
        return
    try:
        fd = sys.stdin.fileno()
        saved = termios.tcgetattr(fd)
    except (termios.error, ValueError):
        yield
        return
    quiet = saved[:]
    quiet[3] &= ~termios.ECHO
    termios.tcsetattr(fd, termios.TCSANOW, quiet)
    try:
        yield
    finally:
        termios.tcsetattr(fd, termios.TCSANOW, saved)


def write(text):
    sys.stdout.write(text)
    sys.stdout.flush()


def width():
    return shutil.get_terminal_size().columns


class InteractiveMode:
    def __init__(self, session):
        self.session = session
        self.writer = None  # the streaming text block being written, if any
        self.working = False  # whether the "Working..." line is on screen
        self.tool_box_height = 0
        session.subscribe(self.on_event)

    def run(self):
        self.print_header()
        while True:
            text = self.read_input()
            if text is None:
                break
            text = text.strip()
            if not text:
                continue
            if text.startswith("/"):
                if not self.command(text):
                    break
                continue
            try:
                with no_echo():
                    self.session.prompt(text)
            except KeyboardInterrupt:
                self.clear_working()
                write(f"\n {ERROR}Operation aborted{RESET}\n")
        write("\n")

    # Header and editor -----------------------------------------------------------------------------

    def print_header(self):
        top = f"{fg(*CORAL)}{bg(*BLUE)}▀{RESET}{fg(*CORAL)}▀█{RESET}    {fg(*MINT)}▄▀{RESET} {fg(*CORAL)}▀▀█{RESET}"
        bottom = f"{fg(*BLUE)}█▀{RESET} {fg(*YELLOW)}█{RESET} {fg(*MINT)}▄▀{RESET}   {fg(*CORAL)}█▄▄{RESET}"
        hints = " · ".join(["ctrl+c interrupt", "ctrl+d exit", "/help commands"])
        write(f" {top} {DIM}v{__version__} (python){RESET}\n {bottom} {DIM}{hints}{RESET}\n\n")
        sources = self.session.extensions.sources
        if sources:
            write(f"{WARNING}[Extensions]{RESET}\n" + "".join(f"{DIM}  {name}{RESET}\n" for name in sources))
        else:
            write(f" {DIM}No tools loaded: the model cannot read or change files. Add tools with -e <file.py>.{RESET}\n")

    def read_input(self):
        """Draw the editor (a line between two borders) and the footer, and read one line into it."""
        w = width()
        border = f"{DIM}{'─' * w}{RESET}"
        cwd, stats = self.footer(w)
        write(f"\n{border}\n\n{border}\n{cwd}\n{stats}\x1b[3A\r")  # back up to the empty line
        try:
            text = input()
        except EOFError:  # ctrl+d
            write("\r\x1b[2A\x1b[J")
            return None
        except KeyboardInterrupt:  # ctrl+c clears the editor
            write("\r\x1b[2A\x1b[J")
            return ""
        rows = len(text) // w + 1
        write(f"\x1b[{rows + 2}A\r\x1b[J")  # remove the editor; the message is drawn as a block instead
        return text

    def footer(self, w):
        cwd = self.session.cwd
        home = os.path.expanduser("~")
        if cwd.startswith(home):
            cwd = "~" + cwd[len(home):]
        usage, model = self.session.usage, self.session.model
        percent = 100 * usage["context"] / model["context_window"]
        left = f"{percent:.1f}%/{tokens(model['context_window'])}"
        if usage["input"]:
            left = f"↑{tokens(usage['input'])} ↓{tokens(usage['output'])} {left}"
        right = model["id"]
        return f"{DIM}{cwd}{RESET}", f"{DIM}{left}{' ' * max(1, w - len(left) - len(right))}{right}{RESET}"

    def command(self, text):
        """Handle a slash command. Returns False to exit."""
        name = text.split()[0]
        if name in ("/quit", "/exit"):
            return False
        if name == "/new":
            self.session.new_session()
            write(f"\n {DIM}New session started{RESET}\n")
        elif name == "/help":
            write(f"\n {DIM}/new  start a new session\n /quit exit pi2{RESET}\n")
        else:
            write(f"\n {ERROR}Unknown command {name}. Try /help.{RESET}\n")
        return True

    # Session events --------------------------------------------------------------------------------

    def on_event(self, event):
        kind = event["type"]
        if kind == "message_start":
            write(f"\n {DIM}⠋ Working...{RESET}")
            self.working = True
        elif kind == "message_update":
            self.clear_working()
            delta = event["event"]
            style = f"{DIM}{ITALIC}" if delta["type"] == "thinking_delta" else ""
            if self.writer is None or self.writer.style != style:
                if self.writer:
                    self.writer.end()
                self.writer = StreamWriter(style, width())
            self.writer.write(delta["delta"])
        elif kind == "message_end":
            self.clear_working()
            message = event["message"]
            if message["role"] == "user":
                self.print_box(USER_BG, [message["content"]])
            elif message["role"] == "assistant":
                if self.writer:
                    self.writer.end()
                    self.writer = None
                if message["stop_reason"] == "error":
                    write(f"\n {ERROR}Error: {message['error_message']}{RESET}\n")
                elif message["stop_reason"] == "aborted":
                    write(f"\n {ERROR}Operation aborted{RESET}\n")
        elif kind == "tool_execution_start":
            self.clear_working()
            self.tool_box_height = self.print_box(TOOL_BG["pending"], [tool_title(event["tool_call"])])
        elif kind == "tool_execution_end":
            result = event["result"]
            lines = result["content"].splitlines()
            preview = [f"{ERROR if result['is_error'] else MUTED}{line}" for line in lines[:PREVIEW_LINES]]
            if len(lines) > PREVIEW_LINES:
                preview.append(f"{DIM}... ({len(lines) - PREVIEW_LINES} more lines)")
            write(f"\x1b[{self.tool_box_height}A\r\x1b[J")  # redraw the pending box with its result
            status = "error" if result["is_error"] else "success"
            self.print_box(TOOL_BG[status], [tool_title(event["tool_call"]), *(["", *preview] if preview else [])])

    def print_box(self, background, lines):
        """A full-width block with a background color and a padding line above and below. Returns its height."""
        w = width()
        rows = [""]
        for line in lines:
            rows.extend(wrap_plain(line, w - 2) or [""])
        rows.append("")
        # A reset inside a row would also clear the background, so the background follows every reset.
        out = "".join(
            f"{background} {row.replace(RESET, RESET + background)}{background}{' ' * max(0, w - 1 - visible_length(row))}{RESET}\n"
            for row in rows
        )
        write("\n" + out)
        return len(rows) + 1

    def clear_working(self):
        if self.working:
            write("\r\x1b[2K\x1b[1A")
            self.working = False


class StreamWriter:
    """Writes streamed text word by word, wrapped to the terminal width with one column of padding."""

    def __init__(self, style, width):
        self.style = style
        self.width = width
        self.word = ""
        self.column = 1
        self.started = False
        write("\n ")

    def write(self, text):
        for char in text:
            if not self.started and char in " \n":
                continue  # skip leading whitespace
            self.started = True
            if char == "\n":
                self.flush_word()
                self.out("\n ")
                self.column = 1
            elif char == " ":
                self.flush_word()
                if self.column < self.width - 1:
                    self.out(" ")
                    self.column += 1
            else:
                self.word += char
        sys.stdout.flush()

    def flush_word(self):
        if not self.word:
            return
        if self.column + len(self.word) > self.width - 1 and self.column > 1:
            self.out("\n ")
            self.column = 1
        self.out(self.word)
        self.column += len(self.word)
        self.word = ""

    def out(self, text):
        sys.stdout.write(f"{self.style}{text}{RESET}")

    def end(self):
        self.flush_word()
        write("\n")


def tool_title(call):
    """The tool's name in bold and its main argument, as Pi's renderers show them."""
    args = call.get("arguments") or {}
    if "command" in args:
        return f"{BOLD}$ {args['command']}{RESET}"
    title = f"{BOLD}{call['name']}{RESET}"
    if "path" in args:
        return f"{title} {ACCENT}{args['path']}{RESET}"
    return f"{title} {DIM}{' '.join(f'{k}={v!r}' for k, v in args.items())}{RESET}"


def visible_length(text):
    """Length on screen: escape codes take no columns."""
    length, escape = 0, False
    for char in text:
        if char == "\x1b":
            escape = True
        elif escape:
            escape = char != "m"
        else:
            length += 1
    return length


def wrap_plain(line, w):
    """Split a line into rows of at most w visible columns, at spaces. Styled lines are cut, not wrapped."""
    if "\x1b" in line:
        return [line] if visible_length(line) <= w else [cut(line, w)]
    return textwrap.wrap(line, w, replace_whitespace=False, drop_whitespace=False) or [""]


def cut(text, w):
    out, length, escape = "", 0, False
    for char in text:
        if char == "\x1b":
            escape = True
        if escape or length < w - 1:
            out += char
            length += 0 if escape else 1
        if escape and char == "m":
            escape = False
    return out + "…"


def tokens(n):
    """Token counts as Pi's footer shows them: 586, 1.2k, 33k."""
    if n < 1000:
        return str(n)
    return f"{n / 1000:.1f}k" if n < 10000 else f"{round(n / 1000)}k"
