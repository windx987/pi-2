"""Extensions: how tools get into pi2.

An extension is a Python file with a function `extension(pi)`. Pass a file or a folder with -e. A
folder loads every top-level `.py` file in sorted order, skipping names that start with `_`. pi2
calls each `extension(pi)` with an ExtensionAPI, which the extension uses to register tools and
listen to events. This mirrors Pi's `export default function (pi: ExtensionAPI)`.
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
        """Load an extension file, or every top-level .py file in a folder."""
        path = Path(path).expanduser().resolve()

        if path.is_dir():
            files = sorted(
                file
                for file in path.iterdir()
                if file.is_file()
                and file.suffix == ".py"
                and not file.name.startswith("_")
                and not file.name.startswith(".")
            )
            if not files:
                raise SystemExit(f"No extension files found in {path}")
            for file in files:
                self.load_file(file)
            return

        if not path.is_file():
            raise SystemExit(f"Extension path not found: {path}")
        self.load_file(path)

    def load_file(self, path):
        """Load one extension file and call its extension(pi) function."""
        path = Path(path).expanduser().resolve()
        module_name = f"pi2_extension_{path.stem}_{len(self.sources)}"
        spec = importlib.util.spec_from_file_location(module_name, path)
        if spec is None or spec.loader is None:
            raise SystemExit(f"Cannot load extension: {path}")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        extension = getattr(module, "extension", None)
        if not callable(extension):
            raise SystemExit(f'{path}: add a function named "extension(pi)".')
        extension(self)
        self.sources.append(path.name)
