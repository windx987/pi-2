# Exercises: build the coding tools

The workshop edition of Pi ships without coding tools. Start it and ask it to read a file: it cannot, because the model is offered no tools. In these exercises you give it four tools, one at a time, written as Pi extensions:

| Exercise | Tool | You learn |
|---|---|---|
| [01-read](01-read/README.md) | `read` | Arguments, filesystem access, error results |
| [02-write](02-write/README.md) | `write` | Structured input, validation, filesystem writes |
| [03-edit](03-edit/README.md) | `edit` | Exact matching, uniqueness, diffs, safe changes |
| [04-bash](04-bash/README.md) | `bash` | Processes, output streams, exit codes, isolation |

Each exercise directory has a `README.md` with the steps and a `starter.ts`: an extension whose tool is already defined and registered, with its JSON Schema written. You implement `execute()`.

The starters are TypeScript. If you have not used it before, read [TypeScript for the workshop](../typescript/README.md) first.

## Setup (before the workshop)

```bash
npm install --ignore-scripts
npm run build
docker pull node:22-bookworm-slim     # for exercise 04: Docker Desktop, or `colima start` with Colima
```

## Model: Gemma 4 through Ollama

The workshop uses an open model served by [Ollama](https://ollama.com). Pick the variant that fits your machine:

| Model | Runs | Needs |
|---|---|---|
| `gemma4:31b` | Locally | About 20 GB of free memory (for example a 32 GB Mac) |
| `gemma4:12b` | Locally | About 8 GB of free memory (works on a 16 GB M1) |

Ollama gives local models a 4096-token context by default and silently cuts longer requests, which is too small for Pi's system prompt, tool definitions and file contents. Create a variant with a larger context once:

```bash
ollama pull gemma4:12b                 # or gemma4:31b
printf 'FROM gemma4:12b\nPARAMETER num_ctx 32768\n' > Modelfile
ollama create gemma4-workshop:12b -f Modelfile
```

Tell Pi about the model in `~/.pi/agent/models.json`:

```json
{
  "$schema": "https://pi.dev/schemas/models.schema.json",
  "providers": {
    "ollama": {
      "baseUrl": "http://localhost:11434/v1",
      "api": "openai-completions",
      "apiKey": "ollama",
      "compat": { "supportsDeveloperRole": false },
      "models": [
        { "id": "gemma4-workshop:12b", "name": "Gemma 4 12B (local, 32k)", "contextWindow": 32768, "maxTokens": 8192 }
      ]
    }
  }
}
```

Start Pi with `--model ollama/gemma4-workshop:12b`, or choose the model with `/model`. Any other provider Pi supports works too (`/login`, or an API key such as `ANTHROPIC_API_KEY`).

## Work on a copy of the playground

The agent changes files. Run it in a copy of [the playground](../playground/), never in the repository. Keep the copy under your home directory: Docker runtimes such as Colima share only the home directory with containers, and a workspace elsewhere (for example in `/tmp`) appears empty inside the container.

```bash
cp -R education/playground ~/pi-workshop
cd ~/pi-workshop
```

## Load your tools

`-e` loads an extension file and can be repeated. From the playground copy, with `REPO` set to the repository path:

```bash
"$REPO/pi-test.sh" -e "$REPO/education/exercises/01-read/starter.ts"
```

After each exercise, add the next file with another `-e`. Edit `starter.ts` in place; type `/reload` in Pi to load your changes without restarting.

## How the pieces fit

```text
defineTool({ name, description, parameters, execute })   your extension
        |  pi.registerTool(...)
        v
AgentSession tool registry  ->  declared to the model with the JSON Schema
        |  model answers with a tool call
        v
arguments validated  ->  your execute(params, ctx)  ->  { content, details, isError? }
        |
        v
tool result sent back to the model  ->  next model turn
```

The tool names (`read`, `write`, `edit`, `bash`) are part of the contract: Pi's TUI renders calls of these names with the original renderers, compaction tracks files by them, and the skills prompt appears once `read` or `bash` is active. Keep the names and argument names (`path`, `content`, `edits`, `command`).

## Reference

The original implementations are in git history at the workshop baseline. Read them after you finish an exercise:

```bash
git show cead615b4:packages/coding-agent/src/core/tools/read.ts
```

See [tool-removal.md](../architecture/tool-removal.md) for what was removed and why.
