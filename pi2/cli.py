"""The command line: reads the options, loads the extensions and starts interactive mode.

    python3 pi2.py --model ollama/gemma4-workshop:12b -e exercises/01-read/read.py
    python3 pi2.py --cwd playground -e exercises/01-read/read.py
    python3 pi2.py --agent-dir .pi-agent -e examples/hello.py

(pi2.py in the repository root runs main() below.)
"""

import argparse
import os
from pathlib import Path

from . import __version__
from .extensions import ExtensionAPI
from .model_runtime import ModelRuntime
from .session import AgentSession
from .tui import InteractiveMode


def resolve_dir(value):
    """Expand ~ and resolve a relative path from the current directory."""
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = Path.cwd() / path
    return path.resolve()


def main():
    parser = argparse.ArgumentParser(prog="pi2", description="pi/2, the Pi Workshop Edition in Python")
    parser.add_argument("--model", help='model as "provider/id" from models.json (default: the first one)')
    parser.add_argument(
        "--cwd",
        help="directory the agent works in (default: the current directory)",
    )
    parser.add_argument(
        "--agent-dir",
        help="directory holding models.json and settings.json (default: ~/.pi/agent)",
    )
    parser.add_argument("-e", "--extension", action="append", default=[], help="load an extension file (repeatable)")
    parser.add_argument("--version", action="version", version=__version__)
    args = parser.parse_args()

    # The same agent directory and models.json as Pi, unless --agent-dir or PI_CODING_AGENT_DIR says otherwise.
    agent_dir = resolve_dir(
        args.agent_dir or os.environ.get("PI_CODING_AGENT_DIR") or Path.home() / ".pi" / "agent"
    )

    cwd = resolve_dir(args.cwd) if args.cwd else Path.cwd()
    if not cwd.is_dir():
        raise SystemExit(f"Working directory not found: {args.cwd}")

    runtime = ModelRuntime(agent_dir)
    model = runtime.find(args.model)

    extensions = ExtensionAPI()
    for path in args.extension:
        extensions.load(path)

    session = AgentSession(runtime, model, extensions, str(cwd), agent_dir)
    InteractiveMode(session).run()
