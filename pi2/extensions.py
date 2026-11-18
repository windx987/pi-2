"""Extensions: how tools get into pi2.

An extension is a Python file with a function `extension(pi)`. pi2 loads each file passed with -e and
calls that function with an ExtensionAPI, which the extension uses to register tools and listen to
events. This mirrors Pi's `export default function (pi: ExtensionAPI)`.
"""

import importlib.util
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable


@dataclass
class Tool:
    name: str
    label: str
    description: str
    parameters: dict  # JSON Schema of the arguments, sent to the model and used for validation
    execute: Callable  # execute(params, ctx) -> str; raise an exception for an error result
    prompt_snippet: str = ""  # one line for the system prompt's tool list
    prompt_guidelines: list = field(default_factory=list)


@dataclass
class ToolContext:
    cwd: str  # the directory the agent works in
    session: object = None  # the AgentSession running the tool: its model, runtime and tools


def define_tool(**fields):
    """Describe a tool. The same fields as Pi's defineTool, in snake_case."""
    return Tool(**fields)


class ExtensionAPI:
    def __init__(self):
        self.tools = {}
        self.handlers = {}
        self.sources = []

    def register_tool(self, tool):
        """Offer a tool to the model. A later tool with the same name replaces the earlier one."""
        self.tools[tool.name] = tool

    def on(self, event, handler):
        """Listen to an event. "tool_call": handler(call, args) may return a reason to block the call."""
        self.handlers.setdefault(event, []).append(handler)

    def load(self, path):
        """Load one extension file and call its extension(pi) function."""
        path = Path(path).resolve()
        spec = importlib.util.spec_from_file_location(f"pi2_extension_{path.stem}", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.extension(self)
        self.sources.append(path.name)
