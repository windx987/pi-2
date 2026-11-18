"""Step 2: the agent session, the center of the application.

Turns your text into a message and starts the agent loop. It owns the conversation, offers the tools
that extensions registered to the model, lets extensions see each tool call, and saves every finished
message to a session file (step 8). pi/2 has no built-in tools: without -e the model gets none.
"""

import json
import os
from datetime import datetime
from pathlib import Path

from . import agent_loop
from .extensions import ToolContext


class AgentSession:
    def __init__(self, runtime, model, extensions, cwd, agent_dir):
        self.runtime = runtime
        self.model = model
        self.extensions = extensions
        self.cwd = cwd
        self.agent_dir = Path(agent_dir)
        self.listeners = []
        self.new_session()

    def new_session(self):
        """Start an empty conversation in a new session file."""
        self.messages = []
        self.usage = {"input": 0, "output": 0, "context": 0}
        slug = self.cwd.strip(os.sep).replace(os.sep, "-") or "root"
        folder = self.agent_dir / "python-sessions" / slug
        self.session_file = folder / f"{datetime.now().strftime('%Y-%m-%dT%H-%M-%S')}.jsonl"
        self.header = {"type": "session", "cwd": self.cwd, "timestamp": datetime.now().isoformat()}

    def subscribe(self, listener):
        self.listeners.append(listener)

    def prompt(self, text):
        """Add the user's message and run the agent loop until the model is done."""
        user = {"role": "user", "content": text}
        self.messages.append(user)
        self.emit({"type": "message_end", "message": user})
        tools = list(self.extensions.tools.values())
        context = {"system_prompt": self.system_prompt(tools), "messages": self.messages, "tools": tools}
        config = {
            "model": self.model,
            "stream_fn": self.runtime.stream_fn,
            "before_tool_call": self.before_tool_call,
            "tool_context": ToolContext(cwd=self.cwd, session=self),
        }
        agent_loop.run(context, config, self.emit)

    def before_tool_call(self, call, args):
        """Step 6: extensions see the call (the "tool_call" event); one returning a reason blocks it."""
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
        for listener in self.listeners:
            listener(event)

    def save(self, message):
        """Step 8: append the finished message to the session file, one JSON object per line."""
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
