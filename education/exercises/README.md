# Exercises: build the coding tools

The workshop edition of Pi ships without coding tools. Start it and ask it to read a file: it cannot, because the model is offered no tools. In these exercises you give it four tools, one at a time, written as Pi extensions:

| Exercise | Tool | You learn |
|---|---|---|
| [01-read](01-read/README.md) | `read` | Arguments, filesystem access, error results |
| [02-write](02-write/README.md) | `write` | Structured input, validation, filesystem writes |
| [03-edit](03-edit/README.md) | `edit` | Exact matching, uniqueness, diffs, safe changes |
| [04-bash](04-bash/README.md) | `bash` | Processes, output streams, exit codes, isolation |

Each exercise directory has a `README.md` with the steps and a `starter.ts`: an extension whose tool is already defined and registered, with its JSON Schema written. You implement `execute()`.

## Setup (before the workshop)

```bash
npm install --ignore-scripts
npm run build
docker pull node:22-bookworm-slim     # for exercise 04
```

Configure a model provider once (`./pi-test.sh`, then `/login`, or set an API key such as `ANTHROPIC_API_KEY`).

## Work on a copy of the playground

The agent changes files. Run it in a copy of [the playground](../playground/), never in the repository:

```bash
cp -R education/playground /tmp/pi-workshop
cd /tmp/pi-workshop
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
