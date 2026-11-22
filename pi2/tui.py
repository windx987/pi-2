"""Step 1: interactive mode, the terminal app.

Waits for your input between two border lines, hands it to the session, and renders every event the
session emits while the answer streams in: thinking, text, and tool calls in colored boxes. The layout
and colors follow Pi's interactive mode and dark theme, drawn with plain ANSI escape codes.

While the agent works the editor stays at the bottom of the screen, so the next message can be typed,
edited and queued as the answer streams above it.
"""

import codecs
import os
import queue
import select
import shutil
import signal
import sys
import textwrap
import threading
import time

try:
    import readline  # noqa: F401  (line editing and history for input())
except ImportError:  # Windows
    pass

try:
    import termios
    import tty
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
SUCCESS = fg(*MINT)
USER_BG = bg(43, 50, 82)
TOOL_BG = {"pending": bg(52, 54, 60), "success": bg(30, 70, 55), "error": bg(88, 48, 40)}
PREVIEW_LINES = 5


def duration(seconds):
    """How long a turn took, as the Finished line shows it: 3.4s, 1m 05s."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes, rest = divmod(int(seconds), 60)
    return f"{minutes}m {rest:02d}s"


def elapsed_seconds(started):
    """The live counter: whole seconds, then minutes once a turn is long."""
    seconds = int(time.monotonic() - started)
    return f"{seconds}s" if seconds < 60 else f"{seconds // 60}m {seconds % 60:02d}s"


def exit_on_signal(signum, frame):
    """Exit through Python's cleanup, so the reader thread gives the terminal its settings back."""
    sys.exit(128 + signum)


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
        self.turn_started = None  # monotonic start of the whole turn
        self.busy = False  # a turn is running: the footer counts its time
        self.status_started = None  # monotonic start of the Working/Compacting line
        self.status_label = ""
        self.status_shown = None  # last whole second drawn in the status line
        self.footer_shown = None
        self.last_stop_reason = None
        self.ticker = None
        self.ticker_stop = threading.Event()
        self.pending = queue.Queue()  # messages typed while the agent is working
        self.reader = None
        self.reader_stop = threading.Event()
        self.quit_requested = False
        self.previous_sigint = None
        self.saved_termios = None
        # The editor at the bottom while the agent works. The reader thread and the agent both write
        # to the terminal, so every write takes this lock.
        self.lock = threading.Lock()
        self.editor = False  # whether the work editor is on screen
        self.editor_text = ""  # what is typed into it, not sent yet
        self.editor_dirty = False  # ctrl+c cleared it from a signal handler: redraw on the next loop
        self.draft = ""  # text left in the work editor when the turn ended
        self.out_line_start = True  # where output continues: a new line, or a column in the last one
        self.out_column = 0
        self.escape = False  # inside an ANSI escape sequence while tracking the output
        self.key_escape = False  # inside an escape sequence typed by the user (arrow keys)
        session.subscribe(self.on_event)

    def run(self):
        self.print_header()
        self.ticker_stop.clear()
        self.ticker = threading.Thread(target=self.tick_loop, daemon=True)
        self.ticker.start()
        self.previous_sigint = signal.getsignal(signal.SIGINT)
        signal.signal(signal.SIGINT, self.on_sigint)
        if termios is not None:
            # A closed terminal or a kill must not leave the terminal without echo.
            signal.signal(signal.SIGTERM, exit_on_signal)
            signal.signal(signal.SIGHUP, exit_on_signal)
        try:
            while not self.quit_requested:
                try:
                    text = self.next_input()
                except KeyboardInterrupt:  # ctrl+c between turns: clear and keep going
                    if self.quit_requested:
                        break
                    continue
                if text is None:
                    break
                text = text.strip()
                if not text:
                    continue
                if text.startswith("/"):
                    if not self.command(text):
                        break
                    continue
                self.run_prompt(text)
        finally:
            self.ticker_stop.set()
            if self.ticker:
                self.ticker.join(timeout=1.0)
                self.ticker = None
            self.stop_read_ahead()
            signal.signal(signal.SIGINT, self.previous_sigint)
        write("\n")

    def next_input(self):
        """Return a queued message first; only draw the editor when nothing is waiting."""
        try:
            return self.pending.get_nowait()
        except queue.Empty:
            return self.read_input()

    def run_prompt(self, text):
        """Run one turn while a reader thread queues anything typed after Enter."""
        self.turn_started = time.monotonic()
        self.footer_shown = None
        self.last_stop_reason = None
        self.busy = True
        self.start_read_ahead()
        outcome = None
        try:
            self.session.prompt(text)
            outcome = "aborted" if self.last_stop_reason == "aborted" else "finished"
        except KeyboardInterrupt:
            outcome = "aborted"
            self.clear_working()
            self.out(f"\n {ERROR}Operation aborted{RESET}\n")
        finally:
            # Stop the clock before tearing down the reader, so its join time is not counted.
            elapsed = time.monotonic() - self.turn_started
            self.busy = False
            self.turn_started = None
            self.clear_working()  # before the editor is erased, or the status line would be left behind
            self.stop_read_ahead()
            if outcome and not self.quit_requested:
                if outcome == "aborted":
                    self.out(f"\n {ERROR}✗ Aborted after {duration(elapsed)}{RESET}\n")
                else:
                    self.out(f"\n {SUCCESS}✓ Finished in {duration(elapsed)}{RESET}\n")

    def on_sigint(self, signum, frame):
        """Ctrl+c: clear queued messages first; stop the agent only when the queue is empty."""
        if self.quit_requested or not self.drain_pending():
            raise KeyboardInterrupt

    def drain_pending(self):
        """Discard queued messages and the half-typed one. Returns whether anything was discarded."""
        drained = False
        while True:
            try:
                self.pending.get_nowait()
            except queue.Empty:
                break
            drained = True
        if self.editor_text:
            self.editor_text = ""
            self.editor_dirty = True
            drained = True
        return drained

    # Reading while the agent works -----------------------------------------------------------------

    def start_read_ahead(self):
        """Draw the editor at the bottom and start reading keys for it.

        Only a terminal can be read a key at a time. Piped input is read line by line as before: a pipe
        would otherwise hand the next line to the reader thread and then look like ctrl+d.
        """
        self.reader_stop.clear()
        self.editor_text = ""
        self.editor_dirty = False
        if termios is None or not self.is_tty():
            return
        with self.lock:
            self.draw_editor()
        self.reader = threading.Thread(target=self.read_ahead, daemon=True)
        self.reader.start()

    def stop_read_ahead(self):
        """Stop reading, restore the terminal, and keep unsent text for the next editor."""
        self.reader_stop.set()
        if self.reader:
            self.reader.join(timeout=1.0)
            self.reader = None
        self.restore_terminal()
        with self.lock:
            self.erase_editor()
        if self.editor_text.strip():
            self.draft = self.editor_text.strip()
        self.editor_text = ""
        self.editor_dirty = False

    def read_ahead(self):
        """Read keys while the agent works. Enter queues the line; /quit interrupts now."""
        try:
            fd = sys.stdin.fileno()
        except (AttributeError, OSError, ValueError):
            return
        raw = termios is not None
        if raw:
            try:
                self.saved_termios = termios.tcgetattr(fd)
                tty.setcbreak(fd)  # one key at a time, no echo; ctrl+c still raises SIGINT
            except (termios.error, ValueError):
                raw = False
        decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")
        buffer = b""
        try:
            while not self.reader_stop.is_set():
                if self.editor_dirty:
                    self.redraw_editor()
                try:
                    ready, _, _ = select.select([fd], [], [], 0.1)
                except (OSError, ValueError):
                    return
                if not ready:
                    continue
                try:
                    chunk = os.read(fd, 4096)
                except OSError:
                    return
                if not chunk:  # ctrl+d, or the input closed
                    self.request_quit()
                    return
                if raw:
                    for key in decoder.decode(chunk):
                        if not self.handle_key(key):
                            return
                else:  # no termios: queue complete lines, as the terminal echoes them
                    buffer += chunk
                    while b"\n" in buffer:
                        line, buffer = buffer.split(b"\n", 1)
                        line = line.decode("utf-8", errors="replace").strip("\r").strip()
                        if line:
                            self.queue(line)
        finally:
            self.restore_terminal()

    def handle_key(self, key):
        """Edit the bottom line with one key. Returns False when the reader should stop."""
        if self.key_escape:  # the rest of an arrow key or another escape sequence: ignore it
            if key.isalpha() or key in "@`~":
                self.key_escape = False
            return True
        if key == "\x1b":
            self.key_escape = True
        elif key in ("\r", "\n"):
            self.submit()
        elif key in ("\x7f", "\b"):
            self.editor_text = self.editor_text[:-1]
            self.redraw_editor()
        elif key == "\x04":  # ctrl+d
            self.request_quit()
            return False
        elif key == "\x03":  # ctrl+c usually arrives as a signal; this is the fallback
            os.kill(os.getpid(), signal.SIGINT)
        elif key.isprintable():
            self.editor_text += key
            self.redraw_editor()
        return True

    def submit(self):
        """Enter: queue the line and leave the editor empty for the next one."""
        line = self.editor_text.strip()
        self.editor_text = ""
        self.redraw_editor()
        if line:
            self.queue(line)

    def queue(self, line):
        """Queue a message, or stop now for /quit."""
        if line in ("/quit", "/exit"):
            self.request_quit()
        else:
            self.pending.put(line)

    def request_quit(self):
        self.quit_requested = True
        os.kill(os.getpid(), signal.SIGINT)

    def restore_terminal(self):
        """Give the terminal its settings back after cbreak; safe to call twice."""
        if self.saved_termios is None:
            return
        try:
            termios.tcsetattr(sys.stdin.fileno(), termios.TCSANOW, self.saved_termios)
        except (termios.error, ValueError, OSError):
            pass
        self.saved_termios = None

    @staticmethod
    def is_tty():
        try:
            return sys.stdin.isatty()
        except (AttributeError, ValueError):
            return False

    # Writing above the editor ----------------------------------------------------------------------

    def out(self, text):
        """Write output above the editor, keeping the editor at the bottom of the screen."""
        with self.lock:
            shown = self.editor
            if shown:
                self.erase_editor()
                self.move_to_output()
            write(text)
            self.track(text)
            if shown:
                self.draw_editor()

    def track(self, text):
        """Remember where output continues: a new line, or a column in the last one."""
        for char in text:
            if self.escape:
                if char.isalpha() or char in "@`~":
                    self.escape = False
            elif char == "\x1b":
                self.escape = True
            elif char == "\n":
                self.out_line_start, self.out_column = True, 0
            elif char == "\r":
                self.out_column = 0
            else:
                self.out_line_start, self.out_column = False, self.out_column + 1

    def erase_editor(self):
        """Clear the editor block. The cursor is on its input line; leave it on the top border."""
        if not self.editor:
            return
        write("\r\x1b[1A\x1b[J")
        self.editor = False

    def move_to_output(self):
        """From the editor's top border, put the cursor where output continues."""
        if not self.out_line_start:
            write("\x1b[1A\r")  # the last output line, one row above the editor
            if self.out_column:
                write(f"\x1b[{self.out_column}C")

    def draw_editor(self):
        """Draw the editor and the footer, and leave the cursor after the typed text.

        The newline only moves the editor below a half-written output line: the output cursor itself
        stays at the end of that line, so out_line_start and out_column are left alone.
        """
        if not self.out_line_start:  # never draw over a half-written line
            write("\n")
        w = width()
        border = f"{DIM}{'─' * w}{RESET}"
        cwd, stats = self.footer(w)
        text = self.visible_text(w)
        write(f"{border}\n{text}\n{border}\n{cwd}\n{stats}")
        write("\x1b[3A\r")  # from the footer back to the input line
        if text:
            write(f"\x1b[{len(text)}C")
        self.editor = True

    def redraw_editor(self):
        """Redraw the bottom line after a keystroke, without touching the output above."""
        with self.lock:
            self.editor_dirty = False
            if not self.editor:
                return
            self.erase_editor()
            self.move_to_output()
            self.draw_editor()

    def visible_text(self, w):
        """The typed text, cut to the terminal width: the end of it when it is longer."""
        limit = max(1, w - 2)
        if len(self.editor_text) <= limit:
            return self.editor_text
        return "…" + self.editor_text[-(limit - 1):]

    # Header and editor -----------------------------------------------------------------------------

    def print_header(self):
        top = f"{fg(*CORAL)}{bg(*BLUE)}▀{RESET}{fg(*CORAL)}▀█{RESET}    {fg(*MINT)}▄▀{RESET} {fg(*CORAL)}▀▀█{RESET}"
        bottom = f"{fg(*BLUE)}█▀{RESET} {fg(*YELLOW)}█{RESET} {fg(*MINT)}▄▀{RESET}   {fg(*CORAL)}█▄▄{RESET}"
        hints = " · ".join(["enter send/queue", "ctrl+c interrupt", "ctrl+d exit", "/help commands"])
        write(f" {top} {DIM}v{__version__} (python){RESET}\n {bottom} {DIM}{hints}{RESET}\n\n")
        sources = self.session.extensions.sources
        if sources:
            write(f"{WARNING}[Extensions]{RESET}\n" + "".join(f"{DIM}  {name}{RESET}\n" for name in sources))
        else:
            write(f" {DIM}No tools loaded: the model cannot read or change files. Add tools with -e <file-or-folder>.{RESET}\n")

    def read_input(self):
        """Draw the editor (a line between two borders) and the footer, and read one line into it."""
        if self.draft:  # text typed while the agent worked: edit it with the same editor
            return self.read_draft()
        write("\r\x1b[2K")
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

    def read_draft(self):
        """Read one line into the editor, starting from the draft. The cursor keys are not handled."""
        self.editor_text, self.draft = self.draft, ""
        if termios is None or not self.is_tty():
            return self.read_input_fallback()
        with self.lock:
            if self.out_line_start:  # the usual blank line between the output and the editor
                write("\n")
            self.draw_editor()
        decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")
        fd = sys.stdin.fileno()
        try:
            self.saved_termios = termios.tcgetattr(fd)
            tty.setcbreak(fd)
        except (termios.error, ValueError, OSError):
            self.saved_termios = None
            return self.read_input_fallback()
        previous_sigint = signal.getsignal(signal.SIGINT)
        signal.signal(signal.SIGINT, signal.default_int_handler)  # here ctrl+c clears this line
        try:
            while True:
                ready, _, _ = select.select([fd], [], [], None)
                if not ready:
                    continue
                chunk = os.read(fd, 4096)
                if not chunk:  # ctrl+d
                    with self.lock:
                        self.erase_editor()
                    return None
                for key in decoder.decode(chunk):
                    if key in ("\r", "\n"):
                        text, self.editor_text = self.editor_text, ""
                        with self.lock:
                            self.erase_editor()
                        return text
                    elif key == "\x04":  # ctrl+d
                        with self.lock:
                            self.erase_editor()
                        return None
                    elif key in ("\x7f", "\b"):
                        self.editor_text = self.editor_text[:-1]
                        self.redraw_editor()
                    elif key.isprintable():
                        self.editor_text += key
                        self.redraw_editor()
        except KeyboardInterrupt:  # ctrl+c clears the editor
            self.editor_text = ""
            with self.lock:
                self.erase_editor()
            return ""
        finally:
            signal.signal(signal.SIGINT, previous_sigint)
            self.restore_terminal()

    def read_input_fallback(self):
        """Without a terminal to put in cbreak, use the ordinary editor and keep the draft in front."""
        draft = self.draft or self.editor_text
        self.draft = ""
        self.editor_text = ""
        with self.lock:
            self.erase_editor()
        text = self.read_input()
        return text if text is None else draft + text

    def footer(self, w):
        cwd = self.session.cwd
        home = os.path.expanduser("~")
        if cwd.startswith(home):
            cwd = "~" + cwd[len(home):]
        usage, model = self.session.usage, self.session.model
        percent = 100 * self.session.context_tokens() / model["context_window"]
        left = f"{usage['context']} / {tokens(model['context_window'])} ({percent:.1f}%)"
        if usage["input"]:
            left = f"↑{tokens(usage['input'])} ↓{tokens(usage['output'])} {left}"
        if self.busy and not self.working and self.turn_started is not None:
            # The status line is gone while the answer streams: keep the live counter in the footer.
            left = f"⠋ {elapsed_seconds(self.turn_started)}  {left}"
        right = f"{model['provider']}/{model['id']}"
        return f"{DIM}{cwd}{RESET}", f"{DIM}{left}{' ' * max(1, w - len(left) - len(right))}{right}{RESET}"

    def command(self, text):
        """Handle a slash command. Returns False to exit."""
        name, *args = text.split()
        if name in ("/quit", "/exit"):
            return False
        if name == "/new":
            self.session.new_session()
            self.out(f"\n {DIM}New session started{RESET}\n")
        elif name == "/compact":
            self.compact(text[len(name):].strip() or None)
        elif name == "/model":
            self.select_model(args)
        elif name == "/context":
            self.context()
        elif name == "/help":
            self.out(
                f"\n {DIM}/compact [focus] summarize older messages to free context\n"
                f" /context       show how full the context window is, and with what\n"
                f" /model [id]    list models in settings.json; switch with a number or provider/id\n"
                f" /new           start a new session\n /quit          exit pi2{RESET}\n"
            )
        else:
            self.out(f"\n {ERROR}Unknown command {name}. Try /help.{RESET}\n")
        return True

    def compact(self, instructions):
        """/compact: summarize the older messages now, optionally focused on what the user names."""
        self.start_read_ahead()  # the editor stays usable while the summary is written
        try:
            if self.session.compact(instructions) is None:
                self.out(f"\n {DIM}Nothing to compact yet: the conversation is shorter than what is kept.{RESET}\n")
        except KeyboardInterrupt:
            self.clear_working()
            self.out(f"\n {ERROR}Compaction aborted{RESET}\n")
        except RuntimeError as error:
            self.clear_working()
            self.out(f"\n {ERROR}{error}{RESET}\n")
        finally:
            self.stop_read_ahead()

    def select_model(self, args):
        """/model lists the models in settings.json; /model <number or provider/id> switches."""
        runtime = self.session.runtime
        if not args:
            rows = []
            for number, model in enumerate(runtime.models, 1):
                current = model is self.session.model
                marker = f"{ACCENT}●{RESET}" if current else " "
                label = f"{model['provider']}/{model['id']}"
                rows.append(f" {marker} {number}. {ACCENT if current else ''}{label}{RESET} {DIM}{model['name']}{RESET}")
            self.out("\n" + "\n".join(rows) + f"\n {DIM}Switch with /model <number> or /model <provider/id>.{RESET}\n")
            return
        model = runtime.match(args[0])
        if model is None:
            self.out(f"\n {ERROR}No model {args[0]} in settings.json. Type /model to list them.{RESET}\n")
            return
        self.session.set_model(model)  # the next request uses it; the conversation stays
        self.out(f"\n {DIM}Model:{RESET} {ACCENT}{model['provider']}/{model['id']}{RESET}\n")

    def context(self):
        """/context: how full the context window is, where compaction starts, and what fills the window."""
        session = self.session
        window, settings = session.model["context_window"], session.compaction_settings
        used = session.context_tokens()
        threshold = window - settings["reserve_tokens"]
        when = f"compacts above {tokens(threshold)}" if settings["enabled"] else "automatic compaction is off"
        # A bar of the window: the context so far, and a mark where compaction starts.
        bar = ["█" if i < round(40 * used / window) else "░" for i in range(40)]
        if settings["enabled"]:
            bar[min(39, round(40 * threshold / window))] = "│"
        rows = [f"{BOLD}Context{RESET} {DIM}about {tokens(used)} of {tokens(window)} tokens ({100 * used / window:.0f}%) · {when}{RESET}",
                f"{ACCENT}{''.join(bar)}{RESET}", ""]
        for label, n, count in session.context_parts():
            if not count:
                continue
            if label in ("system prompt", "tools"):
                unit = f"({count})" if label == "tools" else ""
            else:
                unit = f"({count} message{'s' if count > 1 else ''})"
            rows.append(f"{label:<15}{tokens(n):>7}  {DIM}{unit}{RESET}")
        rows += ["", f"{DIM}Parts are estimates (4 characters per token).{RESET}"]
        self.print_box(TOOL_BG["pending"], rows)

    # Session events --------------------------------------------------------------------------------

    def on_event(self, event):
        kind = event["type"]
        if kind == "message_start":
            self.start_status("Working...")
        elif kind == "message_update":
            self.clear_working()
            delta = event["event"]
            style = f"{DIM}{ITALIC}" if delta["type"] == "thinking_delta" else ""
            if self.writer is None or self.writer.style != style:
                if self.writer:
                    self.writer.end()
                self.writer = StreamWriter(style, width(), self.out)
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
                self.last_stop_reason = message["stop_reason"]
                if message["stop_reason"] == "error":
                    self.out(f"\n {ERROR}Error: {message['error_message']}{RESET}\n")
                elif message["stop_reason"] == "aborted":
                    self.out(f"\n {ERROR}Operation aborted{RESET}\n")
                elif message["stop_reason"] == "length":
                    self.out(f"\n {ERROR}Response was truncated before completion.{RESET}\n")
        elif kind == "compaction_start":
            why = {"manual": "Compacting", "threshold": "Context is filling up", "overflow": "Context too long"}
            self.start_status(f"{why[event['reason']]}: summarizing older messages...")
        elif kind == "compaction_end":
            self.clear_working()
            if "error" in event:
                self.out(f"\n {ERROR}{event['error']}{RESET}\n")
            else:
                before, after = event["message"]["tokens_before"], event["tokens_after"]
                summary = event["message"]["summary"].splitlines()
                preview = [f"{MUTED}{line}" for line in summary[:PREVIEW_LINES]]
                if len(summary) > PREVIEW_LINES:
                    preview.append(f"{DIM}... ({len(summary) - PREVIEW_LINES} more lines)")
                count = f"{event['summarized']} message{'s' if event['summarized'] > 1 else ''}"
                title = f"{BOLD}Compacted{RESET} {DIM}{count}, {tokens(before)} → about {tokens(after)} tokens{RESET}"
                self.print_box(TOOL_BG["pending"], [title, "", *preview])
        elif kind == "tool_execution_start":
            self.clear_working()
            self.tool_box_height = self.print_box(TOOL_BG["pending"], [tool_title(event["tool_call"])])
        elif kind == "tool_execution_end":
            result = event["result"]
            lines = result["content"].splitlines()
            preview = [f"{ERROR if result['is_error'] else MUTED}{line}" for line in lines[:PREVIEW_LINES]]
            if len(lines) > PREVIEW_LINES:
                preview.append(f"{DIM}... ({len(lines) - PREVIEW_LINES} more lines)")
            self.out(f"\x1b[{self.tool_box_height}A\r\x1b[J")  # redraw the pending box with its result
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
        self.out("\n" + out)
        return len(rows) + 1

    def clear_working(self):
        """Remove the "Working..." line, keeping the editor below it where it is."""
        if not self.working:
            return
        with self.lock:
            # Inside the lock, so the ticker cannot redraw the line after it was erased.
            self.working = False
            self.status_label = ""
            self.status_started = None
            self.status_shown = None
            if self.editor:
                self.erase_editor()  # cursor on the editor's top border, one row under the spinner
                write("\x1b[1A\r\x1b[2K")  # up to the spinner, clear it
                write("\x1b[1A\r")  # up to the blank line above it, where the answer starts
                self.out_line_start, self.out_column = True, 0
                self.draw_editor()
            else:
                write("\r\x1b[2K\x1b[1A")
                self.out_line_start, self.out_column = True, 0

    # Live status line and timer --------------------------------------------------------------------

    def start_status(self, label):
        """Show a ticking status line above the editor, replacing one that is already there."""
        if self.working:
            self.clear_working()
        self.status_label = label
        self.status_started = time.monotonic()
        self.status_shown = None
        self.out("\n" + self.status_text())
        self.working = True  # only after the line is on screen, so the ticker cannot redraw a stale row

    def status_text(self):
        return f" {DIM}⠋ {self.status_label} {elapsed_seconds(self.status_started)}{RESET}"

    def tick_loop(self):
        """Once a second, refresh the live counter: the status line, or the footer when it is gone."""
        while not self.ticker_stop.wait(0.25):
            self.tick()

    def tick(self):
        started = self.status_started
        if self.working and started is not None:
            shown = int(time.monotonic() - started)
            if shown != self.status_shown:
                self.status_shown = shown
                self.redraw_status()
        elif self.busy and self.turn_started is not None:
            shown = int(time.monotonic() - self.turn_started)
            if shown != self.footer_shown:
                self.footer_shown = shown
                if self.editor:
                    self.redraw_editor()

    def redraw_status(self):
        """Rewrite the status line in place, above the editor, without moving the answer."""
        with self.lock:
            if not self.working:
                return
            text = self.status_text()
            if self.editor:
                self.erase_editor()
                write("\x1b[1A\r\x1b[2K")  # from the editor's top border up to the status line
                write(text)
                self.track(text)
                self.draw_editor()  # writes the newline first, because out_line_start is False
            else:
                write("\r\x1b[2K" + text)
                self.track(text)


class StreamWriter:
    """Writes streamed text word by word, wrapped to the terminal width with one column of padding."""

    def __init__(self, style, width, out):
        self.style = style
        self.width = width
        self.emit = out  # writes above the work editor when it is on screen
        self.word = ""
        self.column = 1
        self.started = False
        self.emit("\n ")

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
        word, self.word = self.word, ""
        if self.column + len(word) > self.width - 1 and self.column > 1:
            self.out("\n ")
            self.column = 1
        while len(word) > self.width - 1 - self.column:
            # A word longer than a line (a path, a URL) is cut, so the terminal never wraps by itself:
            # the editor's cursor arithmetic assumes every row break is one we wrote.
            take = max(1, self.width - 1 - self.column)
            self.out(word[:take])
            word = word[take:]
            self.out("\n ")
            self.column = 1
        self.out(word)
        self.column += len(word)

    def out(self, text):
        self.emit(f"{self.style}{text}{RESET}")

    def end(self):
        self.flush_word()
        self.emit("\n")


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
