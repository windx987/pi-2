"""The agent session, the center of the application.

Turns your text into a message and starts the agent loop. It owns the conversation, offers the tools
that extensions registered to the model, lets extensions see each tool call, and saves every finished
message to a session file. pi/2 has no built-in tools: without -e the model gets none.
Around the loop it keeps the conversation inside the context window: see compaction.py.
"""

import json
import os
from datetime import datetime
from pathlib import Path

from . import agent_loop, compaction
from .extensions import ToolContext


class AgentSession:
    def __init__(self, runtime, model, extensions, cwd, agent_dir):
        self.runtime = runtime
        self.model = model
        self.extensions = extensions
        self.cwd = cwd
        self.agent_dir = Path(agent_dir)
        self.listeners = []
        self.compaction_settings = compaction.load_settings(agent_dir, model.get("context_window", 128000))
        self.new_session()

    def new_session(self):
        """Start an empty conversation in a new session file."""
        self.messages = []
        self.usage = {"input": 0, "output": 0, "context": 0}
        self.counted = 0  # messages[:counted] are in usage["context"]; later ones are only estimated
        # Model tokens per estimated token, from the model's last count. Four characters per token is
        # right for prose, but logs, numbers and IDs have about twice as many tokens.
        self.ratio = 1.0
        slug = self.cwd.strip(os.sep).replace(os.sep, "-") or "root"
        folder = self.agent_dir / "python-sessions" / slug
        self.session_file = folder / f"{datetime.now().strftime('%Y-%m-%dT%H-%M-%S')}.jsonl"
        self.header = {"type": "session", "cwd": self.cwd, "timestamp": datetime.now().isoformat()}

    def subscribe(self, listener):
        self.listeners.append(listener)

    def prompt(self, text):
        """Add the user's message and run the agent loop until the model is done."""
        self.auto_compact("threshold")
        user = {"role": "user", "content": text}
        self.messages.append(user)
        self.emit({"type": "message_end", "message": user})
        tools = list(self.extensions.tools.values())
        context = {"system_prompt": self.system_prompt(tools), "messages": self.messages, "tools": tools}
        config = {
            "model": self.model,
            "stream_fn": self.runtime.stream_fn,
            "before_tool_call": self.before_tool_call,
            # Between turns, after the tool results: compact if they filled the window (Pi's prepareNextTurn).
            "prepare_next_turn": lambda: self.auto_compact("threshold"),
            "tool_context": ToolContext(cwd=self.cwd, session=self),
        }
        agent_loop.run(context, config, self.emit)
        last = self.messages[-1]
        if compaction.is_context_overflow(last) and self.compaction_settings["enabled"]:
            # The request did not fit: drop the failed answer, compact, and try once more.
            self.messages.pop()
            self.counted = min(self.counted, len(self.messages))
            if self.auto_compact("overflow", force=True):
                agent_loop.run(context, config, self.emit)

    def context_tokens(self):
        """Tokens the next request sends: the model's last count plus an estimate of what came after."""
        tokens = self.usage["context"] + self.estimate(self.messages[self.counted:])
        if self.counted == 0:  # no count from the model yet: estimate the system prompt and tools as well
            system, tools = self.context_parts()[:2]
            tokens += system[1] + tools[1]
        return tokens

    def estimate(self, messages):
        """Estimated tokens of messages: four characters per token, scaled by the model's last count."""
        return round(self.ratio * sum(compaction.estimate_tokens(m) for m in messages))

    def fixed_parts(self):
        """Unscaled estimates of the system prompt and the tool schemas, and the number of tools."""
        tools = list(self.extensions.tools.values())
        schemas = json.dumps([[t.name, t.description, t.parameters] for t in tools])
        return len(self.system_prompt(tools)) // 4, len(schemas) // 4, len(tools)

    def context_parts(self):
        """What the next request is made of, for /context: (label, estimated tokens, how many)."""
        system, schemas, count = self.fixed_parts()
        parts = [("system prompt", round(self.ratio * system), 1), ("tools", round(self.ratio * schemas), count)]
        for role, label in [("compaction", "summary"), ("user", "your messages"), ("assistant", "answers"),
                            ("toolResult", "tool results")]:
            messages = [m for m in self.messages if m["role"] == role]
            parts.append((label, self.estimate(messages), len(messages)))
        return parts

    def auto_compact(self, reason, force=False):
        """Compact when the context is over the threshold, or always with force. Returns whether it did."""
        window = self.model.get("context_window", 128000)
        if not force and not compaction.should_compact(self.context_tokens(), window, self.compaction_settings):
            return False
        try:
            return self.compact(reason=reason) is not None
        except RuntimeError as error:  # a failed summary leaves the conversation as it was
            self.emit({"type": "compaction_end", "reason": reason, "error": str(error)})
            return False

    def compact(self, instructions=None, reason="manual"):
        """Summarize the older messages and keep the newest ones. Returns the summary message, or None
        when there is nothing to summarize. /compact calls this; auto_compact() calls it when needed."""
        # find_cut counts four characters per token; keep_recent_tokens are the model's tokens.
        cut = compaction.find_cut(self.messages, self.compaction_settings["keep_recent_tokens"] / self.ratio)
        previous = self.messages[0] if self.messages and self.messages[0]["role"] == "compaction" else None
        old = self.messages[1 if previous else 0:cut]
        if not old:
            return None
        self.emit({"type": "compaction_start", "reason": reason})
        tokens_before = self.context_tokens()
        summary = compaction.summarize(old, previous and previous["summary"], instructions,
                                       self.model, self.runtime.stream_fn)
        summary += compaction.file_lists(old)
        message = {"role": "compaction", "summary": summary, "tokens_before": tokens_before}
        # In place: the running agent loop holds this same list.
        self.messages[:] = [message, *self.messages[cut:]]
        self.usage["context"] = 0
        self.counted = 0
        self.save(message)
        self.emit({"type": "compaction_end", "reason": reason, "message": message,
                   "summarized": len(old), "tokens_after": self.context_tokens()})
        return message

    def before_tool_call(self, call, args):
        """Extensions see the call (the "tool_call" event); one returning a reason blocks it."""
        for handler in self.extensions.handlers.get("tool_call", []):
            reason = handler(call, args)
            if reason:
                return f"Blocked by extension: {reason}"
        return None

    def emit(self, event):
        if event["type"] == "message_end":
            self.save(event["message"])
            usage = event["message"].get("usage")
            if usage and usage["input"]:
                self.usage["input"] += usage["input"]
                self.usage["output"] += usage["output"]
                self.usage["context"] = usage["input"] + usage["output"]
                self.counted = len(self.messages)
                # The request was everything before this answer. Never below 1: an estimate that is too
                # low lets a request overflow, one that is too high only compacts a little early.
                system, schemas, _ = self.fixed_parts()
                estimated = system + schemas + sum(compaction.estimate_tokens(m) for m in self.messages[:-1])
                self.ratio = min(4.0, max(1.0, usage["input"] / estimated))
        for listener in self.listeners:
            listener(event)

    def save(self, message):
        """Append the finished message to the session file, one JSON object per line."""
        new = not self.session_file.exists()
        self.session_file.parent.mkdir(parents=True, exist_ok=True)
        with self.session_file.open("a") as file:
            if new:
                file.write(json.dumps(self.header) + "\n")
            file.write(json.dumps({"type": "message", "message": message}) + "\n")

    def system_prompt(self, tools):
        if tools:
            tool_lines = "\n".join(f"- {t.name}: {t.prompt_snippet or t.description}" for t in tools)
        else:
            tool_lines = "(none: you cannot read, write or run anything. Say so when a task needs it.)"
        guidelines = [g for t in tools for g in t.prompt_guidelines] + ["Be concise in your responses."]
        return "\n".join([
            "You are an expert coding assistant operating inside pi2, a coding agent harness. "
            "You help users by reading files, executing commands, editing code, and writing new files.",
            "",
            "Available tools:",
            tool_lines,
            "",
            "Guidelines:",
            *(f"- {g}" for g in guidelines),
            "",
            f"Current date: {datetime.now().strftime('%Y-%m-%d')}",
            f"Current working directory: {self.cwd}",
        ])
