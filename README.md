<p align="center">
  <img alt="pi/2 logo" src="./assets/logo.svg" width="128">
</p>

# pi/2 Python Workshop

A small coding agent written in standard-library Python. Tools are loaded from Python extensions.

## Setup

Requirements: Python 3.10+ and an OpenAI-compatible provider.

```bash
git clone -b lean https://github.com/windx987/pi-2.git
cd pi-2

# Optional (settings.local.json is in .gitignore)
cp settings.json settings.local.json
# edit settings.local.json
```

No package installation is required.

## Verify

Run from the repository root:

```bash
python3 -m pi2 --help
```

## Run

Load all tools:

```bash
python3 -m pi2 -e tools
```

Start in a playground:

```bash
python3 -m pi2 \
  --cwd playground/01-read \
  -e tools/01-read.py
```

Use private settings with `--settings settings.local.json`.

| Option | Meaning |
|---|---|
| `--cwd DIR` | Agent working directory |
| `--settings FILE` | Settings file |
| `--model ID` | Model as `provider/id` (or its number); default: the first in `settings.json` |
| `-e FILE_OR_DIR` | Extension to load; repeatable |
| `--version` | Print the version |

`--cwd` is not a sandbox. `command` runs as your user, and `read` can read outside it.

## Models

`settings.json` lists providers, each with its models. Add more to switch between them:

```json
{
  "agentDir": "~/.pi/agent",
  "providers": {
    "local": {
      "baseUrl": "http://localhost:8000/v1",
      "apiKey": "local",
      "models": [
        { "id": "local-model", "name": "Local model", "contextWindow": 32768, "maxTokens": 8192 }
      ]
    },
    "remote": {
      "baseUrl": "https://llm.example.com/v1",
      "apiKey": "sk-REPLACE_ME",
      "models": [
        { "id": "example-model", "name": "Example model", "contextWindow": 32768, "maxTokens": 8192 }
      ]
    }
  }
}
```
 - `apiKey` may also name an environment variable, like `"apiKey": "VLLM_API_KEY"`.
 - A session uses one model at a time.
 - The older flat `"provider": { ... }` shape still loads as a single model.

```bash
python3 -m pi2 --model remote/example-model -e tools
```

## Exercises

```bash
python3 exercises/check.py 01
```

See [`exercises/README.md`](exercises/README.md).

```text
playground/01-read/
playground/02-write/
playground/03-edit/
playground/04-search/
playground/05-command/
playground/06-subagents/
```

Reset a playground with:

```bash
git restore playground/01-read
```

## Extensions

An extension registers tools through `extension(pi)`:

```python
from pi2 import ExtensionAPI


def extension(pi: ExtensionAPI):
    pi.register_tool(my_tool)
```

Exercise starters are in `tools/01-read.py` through `tools/06-subagent.py`.

## License

MIT, as the original Pi.
