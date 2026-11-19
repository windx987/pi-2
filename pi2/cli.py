"""The command line: reads the settings, loads the extensions and starts interactive mode.

    python3 -m pi2 -e tools
    python3 -m pi2 --settings settings.local.json -e tools
"""

import argparse
import json
import os
from pathlib import Path

from . import __version__
from .extensions import ExtensionAPI
from .model_runtime import ModelRuntime
from .session import AgentSession
from .tui import InteractiveMode

DEFAULT_AGENT_DIR = Path.home() / ".pi" / "agent"


def default_settings_path():
    """settings.json in the repository root, independent of the current directory."""
    return Path(__file__).resolve().parents[1] / "settings.json"


def resolve_settings_path(value):
    """Expand ~ and resolve a relative --settings path from the current directory."""
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = Path.cwd() / path
    return path.resolve()


def load_settings(path):
    try:
        settings = json.loads(path.read_text())
    except FileNotFoundError:
        raise SystemExit(f"Settings file not found: {path}") from None
    except json.JSONDecodeError as error:
        raise SystemExit(f"Cannot read {path}: {error}") from None

    provider = settings.get("provider")
    if not isinstance(provider, dict):
        raise SystemExit(f'{path}: add a "provider" object.')
    if not provider.get("baseUrl"):
        raise SystemExit(f"{path}: provider.baseUrl is required.")
    if not provider.get("model"):
        raise SystemExit(f"{path}: provider.model is required.")
    return settings


def resolve_agent_dir(settings, settings_path):
    """Resolve agentDir from the settings file. Relative paths are next to settings.json."""
    agent_dir = Path(settings.get("agentDir", DEFAULT_AGENT_DIR)).expanduser()
    if not agent_dir.is_absolute():
        agent_dir = settings_path.parent / agent_dir
    return agent_dir.resolve()


def main():
    parser = argparse.ArgumentParser(prog="pi2", description="pi/2, the Pi Workshop Edition in Python")
    parser.add_argument("--settings", help="settings file (default: settings.json in the repository root)")
    parser.add_argument(
        "-e",
        "--extension",
        action="append",
        default=[],
        help="load an extension file or folder (repeatable)",
    )
    parser.add_argument("--version", action="version", version=__version__)
    args = parser.parse_args()

    settings_path = resolve_settings_path(args.settings) if args.settings else default_settings_path()
    settings = load_settings(settings_path)
    agent_dir = resolve_agent_dir(settings, settings_path)

    runtime = ModelRuntime(settings["provider"])

    extensions = ExtensionAPI()
    for path in args.extension:
        extensions.load(path)

    session = AgentSession(runtime, runtime.model, extensions, os.getcwd(), agent_dir)
    InteractiveMode(session).run()
