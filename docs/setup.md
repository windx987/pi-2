# Install and run

Setup for pi2. The [README](../README.md) has the short version.

You need Python 3.10 or newer (no packages), git, bash, and a model served by [Ollama](https://ollama.com) or [vLLM](https://docs.vllm.ai).

## 1. Python

```bash
python3 --version
```

If it is older or missing, install it:

```bash
# macOS
brew install python@3.12

# Ubuntu, Debian
sudo apt install python3

# Fedora
sudo dnf install python3
```

Nothing else to install: pi2 uses only the standard library. If `python3` still shows the old version, use `python3.12` in its place.

## 2. The code

Clone the `python` branch into `~/pi-2`. If you clone somewhere else, change the path in the commands that follow.

```bash
git clone -b python https://github.com/windx987/pi-2.git ~/pi-2
cd ~/pi-2
```

Check that it starts, without a model:

```bash
python3 pi2.py --version
```

It should print `0.1.0`.

## 3. A model

pi2 talks to any server with an OpenAI-compatible `POST /chat/completions` endpoint, such as Ollama or vLLM. Tell it where in `~/.pi/agent/models.json`, the same file Pi uses:

```json
{
  "providers": {
    "vllm": {
      "baseUrl": "http://localhost:8000/v1",
      "api": "openai-completions",
      "apiKey": "none",
      "models": [
        { "id": "Qwen/Qwen3-8B", "name": "Qwen3 8B", "contextWindow": 32768, "maxTokens": 8192 }
      ]
    }
  }
}
```

Create the folder and keep the file to yourself: it holds your key.

```bash
mkdir -p ~/.pi/agent
chmod 600 ~/.pi/agent/models.json
```

Replace `baseUrl`, `apiKey`, `id` and the limits with your server's values. At a workshop, the instructor gives you the address, key and model id of a shared server.

To keep the config with the project instead, put it in a folder such as `.pi-agent/` (it is in `.gitignore`) and pass `--agent-dir .pi-agent`:

```bash
mkdir -p .pi-agent
cp ~/.pi/agent/models.json .pi-agent/models.json
python3 pi2.py --agent-dir .pi-agent -e examples/hello.py
```

- `contextWindow` is how many tokens the model takes: at least 32k, and what the server really allows. pi2 compacts when the conversation nears it.
- `maxTokens` caps each answer.

[models.md](models.md) has the setups step by step: Ollama on your machine, vLLM on a GPU server, and several models in one file.

## 4. bash (for exercise 03)

Exercise 03's bash tool runs the commands the model writes with bash on your machine, in the working directory, as Pi's own bash tool does. macOS and Linux have bash already. Check that the playground's tests run; the agent runs the same command:

```bash
cd playground
python3 -m unittest     # Ran 2 tests, FAILED (failures=1)
cd ..
```

The failing test is the bug the agent fixes in exercise 04.

Nothing isolates the commands: they can read and change your files and use your network. Work only in `playground/`, load [the permission gate](../playground/README.md#4-a-permission-gate) with your tools, and read each command before the agent's next step. [Exercise 03](../exercises/03-bash/README.md#try-it) has the details.

## 5. Start pi2

Start it from the clone with the example tool:

```bash
python3 pi2.py -e examples/hello.py
```

It starts with the first model in `models.json`. Type `/model` to list the others and `/model 2` to switch, or start with one: `python3 pi2.py --model ollama/gemma4-workshop:12b`.

For the workshop, work in the repository playground. `--cwd playground` points the agent's tools there while the extension paths stay relative to the clone:

```bash
python3 pi2.py --cwd playground -e exercises/01-read/read.py
```

Reset the playground between exercises with `git restore playground && git clean -fd playground`.

| Key or command | Does |
|---|---|
| Enter | Send the message |
| ctrl+c | While the agent works: stop it. In the editor: clear it |
| ctrl+d | Exit (on Windows: ctrl+z, then Enter) |
| `/model` | List the models in `models.json`; `/model <number>` or `/model <provider/id>` switches |
| `/compact [focus]` | Summarize the older messages now to free context; the optional text says what the summary must keep. See [compaction.md](compaction.md) |
| `/context` | Show how full the context window is, where compaction starts, and what fills it. See [compaction.md](compaction.md) |
| `/new`, `/quit`, `/help` | New session, exit, list commands |

Text you type while the agent works waits in the editor for the next message.

`pi2.py` works from any directory, so from another directory start it as `python3 ~/pi-2/pi2.py`. For another Python, run it with that one, such as `python3.12 pi2.py`. To get a `pi2` command instead, run `pip install -e .` once.
