"""The command line: reads the options, loads the extensions and starts interactive mode.

    python3 -m pi2 --model ollama/gemma4-workshop:12b -e exercises/tools.py
"""

import argparse
import os
from pathlib import Path

from . import __version__
from .extensions import ExtensionAPI
from .model_runtime import ModelRuntime
from .session import AgentSession
from .tui import InteractiveMode


def main():
    parser = argparse.ArgumentParser(prog="pi2", description="pi/2, the Pi Workshop Edition in Python")
    parser.add_argument("--model", help='model as "provider/id" from models.json (default: the first one)')
    parser.add_argument("-e", "--extension", action="append", default=[], help="load an extension file (repeatable)")
    parser.add_argument("--version", action="version", version=__version__)
    args = parser.parse_args()

    # The same agent directory and models.json as Pi.
    agent_dir = Path(os.environ.get("PI_CODING_AGENT_DIR", Path.home() / ".pi" / "agent"))
    runtime = ModelRuntime(agent_dir)
    model = runtime.find(args.model)

    extensions = ExtensionAPI()
    for path in args.extension:
        extensions.load(path)

    session = AgentSession(runtime, model, extensions, os.getcwd(), agent_dir)
    InteractiveMode(session).run()
