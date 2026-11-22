"""The command line: reads the settings, loads the extensions and starts interactive mode.

    python3 -m pi2 -e tools
    python3 -m pi2 --cwd playground -e tools
    python3 -m pi2 --settings settings.local.json -e tools
    python3 -m pi2 --model remote/example-model -e tools
"""

import argparse
import json
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

    check_settings(settings, path)
    return settings


def check_settings(settings, path):
    """Require "providers" with models, or the old flat "provider"."""
    providers = settings.get("providers")
    if providers is not None and not isinstance(providers, dict):
        raise SystemExit(f'{path}: "providers" must be an object.')
    if providers:
        for name, provider in providers.items():
            if not isinstance(provider, dict):
                raise SystemExit(f"{path}: provider {name} must be an object.")
            if not provider.get("baseUrl"):
                raise SystemExit(f"{path}: provider {name} needs a baseUrl.")
            models = provider.get("models")
            if not isinstance(models, list) or not models:
                raise SystemExit(f"{path}: provider {name} needs a models array.")
            for model in models:
                if not isinstance(model, dict) or not model.get("id"):
                    raise SystemExit(f'{path}: every model of provider {name} needs an "id".')
        return
    provider = settings.get("provider")
    if not isinstance(provider, dict):
        raise SystemExit(f'{path}: add a "providers" object (or the old "provider").')
    if not provider.get("baseUrl"):
        raise SystemExit(f"{path}: provider.baseUrl is required.")
    if not provider.get("model"):
        raise SystemExit(f"{path}: provider.model is required.")


def resolve_agent_dir(settings, settings_path):
    """Resolve agentDir from the settings file. Relative paths are next to settings.json."""
    agent_dir = Path(settings.get("agentDir", DEFAULT_AGENT_DIR)).expanduser()
    if not agent_dir.is_absolute():
        agent_dir = settings_path.parent / agent_dir
    return agent_dir.resolve()


def main():
    parser = argparse.ArgumentParser(prog="pi2", description="pi/2, the Pi Workshop Edition in Python")
    parser.add_argument("--settings", help="settings file (default: settings.json in the repository root)")
    parser.add_argument("--model", help='model as "provider/id" (or its number); default: the first in settings.json')
    parser.add_argument(
        "--cwd",
        help="directory the agent works in (default: the current directory)",
    )
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

    runtime = ModelRuntime(settings)
    model = runtime.find(args.model)

    extensions = ExtensionAPI()
    for path in args.extension:
        extensions.load(path)

    cwd = Path(args.cwd).expanduser().resolve() if args.cwd else Path.cwd().resolve()
    if not cwd.exists():
        raise SystemExit(f"Working directory not found: {args.cwd}")
    if not cwd.is_dir():
        raise SystemExit(f"Not a directory: {args.cwd}")

    session = AgentSession(runtime, model, extensions, str(cwd), agent_dir)
    InteractiveMode(session).run()
