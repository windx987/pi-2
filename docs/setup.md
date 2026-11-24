# Install and run

Setup for pi2 on macOS and Linux. On Windows, follow [windows.md](windows.md). The [README](../README.md) has the short version.

You need Python 3.10 or newer (no packages), git, a model served by [Ollama](https://ollama.com) or [vLLM](https://docs.vllm.ai), and, for exercise 03, Docker or the no-Docker mode (step 4).

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

## 4. Docker, or the no-Docker mode (for exercise 03)

Exercise 03's bash tool runs the commands the model writes. Choose where; you can switch any time. Exercises 01 and 02 need neither, so you can start before this is set up.

| | Docker (recommended) | No-Docker mode |
|---|---|---|
| Commands run | in a new container that sees only the working directory, without network | with bash on your machine, in the working directory, as Pi's own bash tool does |
| A wrong command can | change the working directory only | reach your files, your network, everything your user may do |
| Setup | option 1 below | option 2 below |
| Start pi2 with | `python3 pi2.py ...` | `PI2_NO_DOCKER=1 python3 pi2.py ...` |

**Option 1: Docker (recommended)**

```bash
docker pull node:22-bookworm-slim
docker run --rm node:22-bookworm-slim node --version
```

Install [Docker Desktop](https://www.docker.com/products/docker-desktop/), or on macOS [Colima](https://github.com/abiosoft/colima) (`brew install colima docker && colima start`), then pull the image once and try it as above. Docker Desktop shares your home directory with its containers; the clone is in `~/pi-2`, so `--cwd playground` stays visible to the container.

**Option 2: no Docker**

The commands run on your machine, so what they call must be installed there. The playground's tests need Node.js 22 or newer, which brings `npm` with it (in option 1 the container image has them):

```bash
# macOS (Homebrew), or the installer from nodejs.org
brew install node

# Linux: nvm, since distribution packages (apt install nodejs) are often too old
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash
nvm install 22                # in a new terminal

node --version                # v22 or newer
npm --version
(cd ~/pi-2/playground && npm test)    # runs the tests: pass 1, fail 1
```

The failing test is the bug the agent fixes in exercise 04. Then turn the mode on:

```bash
export PI2_NO_DOCKER=1     # once per terminal, or put PI2_NO_DOCKER=1 in front of the command that starts pi2
```

The bash tool then runs each command with bash on your machine, in the working directory. `python3 exercises/check.py 03` always runs the "(no Docker)" checks, with or without Docker installed; they show TODO until you write the tool. Because nothing isolates the commands, work only in `playground/`, load [the permission gate](../playground/README.md#4-a-permission-gate) with your tools, and read each command before the agent's next step. [Exercise 03](../exercises/03-bash/README.md#try-it) has the details.

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
