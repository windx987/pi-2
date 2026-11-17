# Tool Removal Plan

Status: decisions made (section 8); source change in progress.
Baseline: upstream commit `cead615b4` (last upstream commit before the workshop-edition changes).

This document lists every built-in coding tool, everything in the repository that depends on one, and what the workshop edition removes, keeps or replaces. It is the checklist for the removal change and the reference for anyone merging upstream later.

Decisions already made:

- Participants build tools as extensions with `pi.registerTool(...)`.
- All built-in coding tools are removed: `read`, `write`, `edit`, `bash`, `grep`, `find`, `ls`, `powershell`.
- The generic tool infrastructure stays: tool interfaces, registry, validation, execution lifecycle, extension API and renderers.
- No placeholder implementations that throw.

## End state in one trace

Today, a user starts `pi` and asks "what is in package.json?":

1. `AgentSession._buildRuntime()` calls `createAllToolDefinitions()`, which builds the 8 built-in tools.
2. `read`, `bash`, `edit`, `write` become active and are declared to the model.
3. The model calls `read({ path: "package.json" })`; the built-in `read` runs.

After the change:

1. `_buildRuntime()` has no built-in tools. With no extensions loaded, no tool is active and the system prompt's tool list is `(none)`.
2. The participant starts `pi -e education/exercises/01-read/read.ts`. The extension calls `pi.registerTool(readTool)`; the tool is active on registration and is declared to the model.
3. The model calls `read({ path: "package.json" })`; the participant's `execute()` runs, and Pi's tool lifecycle (argument validation, `tool_call`/`tool_result` events, rendering, session persistence) handles the rest.

Because the participant's tool uses the name `read`, everything else in Pi that keys on that name keeps working: the built-in TUI renderer, compaction's file tracking and the skills prompt (see [Name-based behavior](#name-based-behavior)).

## 1. Built-in tools and where they are registered

### Implementations

All in `packages/coding-agent/src/core/tools/`.

| Tool | File | Lines | Renderer |
|---|---|---|---|
| `read` | `read.ts` | 363 | `renderers/read.ts` |
| `write` | `write.ts` | 96 | `renderers/write.ts` |
| `edit` | `edit.ts` (+ `edit-diff.ts`, 745) | 221 | `renderers/edit.ts` |
| `bash` | `bash.ts` | 476 | `renderers/bash.ts` |
| `powershell` | `powershell.ts` | 87 | `renderers/bash.ts` (`createShellRenderers("PS>")`) |
| `grep` | `grep.ts` | 337 | `renderers/grep.ts` |
| `find` | `find.ts` | 368 | `renderers/find.ts` |
| `ls` | `ls.ts` | 175 | `renderers/ls.ts` |

Each tool file holds two things:

- **Contract:** the TypeBox parameter schema, the `XToolInput` type (`Static<typeof schema>`), the `XToolDetails` type, the `XOperations` interface (pluggable I/O backend), and the `XToolOptions` type.
- **Implementation:** the default local operations, `execute()`, `createXToolDefinition()`, `createXTool()`, and the prompt snippet and guidelines.

This split matters: the renderers and the typed extension events import only the contract.

### Registration path

```text
core/tools/index.ts
  createAllToolDefinitions(cwd, options)      -> Record<ToolName, ToolDefinition> (all 8)
        |
core/agent-session.ts  _buildRuntime()  (line ~3784)
  baseToolDefinitions = _baseToolsOverride ?? createAllToolDefinitions(...)
  this._baseToolDefinitions = Map(...)
  defaultActiveToolNames = ["read", "bash", "edit", "write"]      (line ~3823)
        |
core/agent-session.ts  _refreshToolRegistry()  (line ~3720)
  toolRegistry = built-in tools, then extension tools set by name   <- an extension tool
                                                                       with the same name
                                                                       replaces the built-in
  active tools = requested names that exist in the registry          <- unknown names ignored
```

The default active names are written in three places:

| Place | Value |
|---|---|
| `core/settings-manager.ts:85` `DEFAULT_TOOL_NAMES` | `["read", "bash", "edit", "write"]` |
| `core/agent-session.ts:~3823` `defaultActiveToolNames` | same literal |
| `core/system-prompt.ts:64` default `selectedTools` | same literal |

## 2. Dependencies on the built-in tools

### 2.1 coding-agent runtime (`packages/coding-agent/src`)

| File | Uses | Action |
|---|---|---|
| `core/agent-session.ts` | `createAllToolDefinitions`; `BashOperations`, `createLocalBashOperations` for the user `!command` shell (`executeBash`, line ~4032) | Replace: base tools become `{}`. Keep the local bash operations (see 3.2). |
| `core/sdk.ts` | imports and re-exports `createReadTool` ... `createPowerShellTool`, `createCodingTools`, `createReadOnlyTools` | Remove those imports and re-exports. Keep `withFileMutationQueue`. |
| `index.ts` (public API, lines ~270-398) | exports all tool factories, definitions, operations types, `generateDiffString`, `generateUnifiedPatch`, `formatReadLineRange` | Remove factory/definition exports. Keep contract types and helpers. |
| `core/extensions/types.ts` | contract types for typed `tool_call` events (`BashToolCallEvent` ... `LsToolCallEvent`, `isToolCallEventType`), `BashOperations` for `user_bash` | Keep. Contract types stay, so no change. |
| `core/bash-executor.ts` | `BashOperations` type | Keep. |
| `core/tools/renderers/*` | contract types (`ReadToolDetails` etc.), `edit-diff.ts` for the edit preview | Keep (see 3.3 for `edit-diff.ts`). |
| `modes/interactive/interactive-mode.ts` | `withBuiltInRenderers`, `TruncationResult` | Keep. |
| `modes/interactive/components/tool-execution.ts`, `tree-selector.ts`, `bash-execution.ts` | `render-utils.ts`, `truncate.ts` helpers | Keep. |
| `cli/file-processor.ts` | `resolveReadPath` from `path-utils.ts` (`@file` arguments) | Keep. |
| `extensions/mcp/*`, `extensions/codemode/*` | `render-utils.ts`, `truncate.ts`, `tool-definition-wrapper.ts` | Keep. Not affected. |
| `core/settings-manager.ts`, `core/system-prompt.ts` | default tool names | Keep the names (see 4). |
| `core/compaction/utils.ts`, `core/export-html/index.ts`, `modes/interactive/components/tree-selector.ts` | tool names only (`"read"`, `"write"`, `"edit"`, ...) | Keep. Works with participant tools of the same name. |

### 2.2 Bundled extensions

`builtin:mcp` and `builtin:codemode` import only helpers (`render-utils.ts`, `truncate.ts`, `tool-definition-wrapper.ts`). They are not affected.

### 2.3 Examples (`packages/coding-agent/examples/extensions`)

These are type-checked by `npm run check` and break when the factories are removed.

| Example | Uses |
|---|---|
| `ssh.ts` | `createReadTool`, `createWriteTool`, `createEditTool`, `createBashTool` with remote operations |
| `gondolin/index.ts` | all factories except powershell, with VM operations |
| `minimal-mode.ts` | all `createXToolDefinition` to restyle rendering |
| `built-in-tool-renderer.ts` | `createRead/Bash/Edit/WriteToolDefinition` to wrap rendering |
| `bash-spawn-hook.ts` | `createBashTool` with a spawn hook |

`truncated-tool.ts` only mentions `grep.ts` in a comment. `preset.ts`, `tools.ts` and `dynamic-tools.ts` use tool names only.

### 2.4 Durable and p2 (separate implementations)

`packages/durable/src/tools/` has its own `read`, `write`, `edit`, `bash`, `powershell` implementations. `apps/p2/plugins/coding-tools` and `apps/p2/plugins/powershell` use them. `apps/p2/plugins/coding-tools/cards.ts` and `apps/p2/src/tui/tools/*` are copies of coding-agent's renderers and do not import them.

None of this is on the workshop path (`pi` from `packages/coding-agent`). Kept (decision 1).

### 2.5 Docs

These document the built-in tools or their factories and need edits: `packages/coding-agent/docs/extensions.md`, `sdk.md`, `cli.md`, `settings.md`, `security.md`, `containerization.md`, `environment-variables.md`, and `packages/coding-agent/README.md`.

## 3. Remove, retain, replace

### 3.1 `core/tools/` file by file

| File | Action | Reason |
|---|---|---|
| `read.ts`, `write.ts`, `edit.ts`, `grep.ts`, `find.ts`, `ls.ts` | Trim to the contract: schema, `Input` and `Details` types. Remove `execute`, operations, options, factories, prompt snippets. | Renderers and typed events import the contract. Keeping the file paths keeps every import unchanged. `Operations` and `Options` only configured the removed factories. |
| `bash.ts`, `powershell.ts` | Trim like the others, but keep `BashOperations`, `createLocalShellOperations`, `createLocalBashOperations`, `createLocalPowerShellOperations`. | The user `!command` shell and the `user_bash` event need a local process backend. This is not the agent tool. |
| `index.ts` | Remove `createTool`, `createToolDefinition`, `createAllTools`, `createAllToolDefinitions`, `createCodingTools(Definitions)`, `createReadOnlyTools(Definitions)`, `ToolsOptions`. Keep `ToolName`, `allToolNames`, contract re-exports, helper re-exports. | `ToolName` keys the renderer table. |
| `renderers/*` | Keep. | A participant tool named `read` gets the built-in `read` renderer through `withBuiltInRenderers()`. Renderers treat `details` as optional. |
| `edit-diff.ts` | Keep for now. Kept (decision 5). | `renderers/edit.ts` uses `computeEditsDiff` for the edit-call preview. |
| `truncate.ts`, `path-utils.ts`, `output-accumulator.ts`, `file-mutation-queue.ts`, `render-utils.ts`, `tool-definition-wrapper.ts` | Keep. | Used by the TUI, CLI, MCP and codemode. They are also public helpers participants may use. |

Why trim in place instead of moving the contract to a new `types.ts`: moving would change the imports in renderers, `extensions/types.ts` and `index.ts`, which is a larger diff against upstream for no behavior gain.

### 3.2 The user shell (`!command`)

`!ls` in the TUI is not an agent tool. It calls `AgentSession.executeBash()`, which uses `createLocalBashOperations()` from `bash.ts`. Removing it would remove a user feature that is unrelated to the exercises, so it stays.

### 3.3 Public API

Removed from `@earendil-works/pi-coding-agent`: `createReadTool`, `createWriteTool`, `createEditTool`, `createBashTool`, `createGrepTool`, `createFindTool`, `createLsTool`, `createPowerShellTool`, every `createXToolDefinition`, `createCodingTools`, `createReadOnlyTools`.

Kept: `defineTool`, `ToolDefinition`, all contract types, `withFileMutationQueue`, truncation helpers, `formatReadLineRange`.

## 4. How the default tool set becomes empty

One code change: in `AgentSession._buildRuntime()`, the base tool definitions become `{}` when there is no `_baseToolsOverride`, instead of calling `createAllToolDefinitions()`.

The default names (`DEFAULT_TOOL_NAMES`, `defaultActiveToolNames`, the system prompt default) stay unchanged:

- Unknown names are ignored when tools are activated (`setActiveToolsByName`: "Unknown and hidden tool names are ignored"), so with no extension loaded nothing is active.
- When a participant extension registers `read`, the name is in the registry and the existing defaults, `defaultTools` setting and `--tools` flag work on it as before.
- Leaving the names alone avoids diffs in three files and in the tests that check them.

`--no-builtin-tools` and `noTools: "builtin"` keep working but have no effect, since there are no built-in tools.

### Name-based behavior

These parts of Pi key on the tool name, so participant tools should use the original names and the original argument names (`path`, `content`, `command`, ...):

| Behavior | Where | Needs |
|---|---|---|
| TUI rendering of calls and results | `withBuiltInRenderers()` | name; `details` in the original shape for full output (optional) |
| Compaction tracks read and modified files | `compaction/utils.ts` | names `read`, `write`, `edit`; argument `path` |
| Skills prompt is included | `system-prompt.ts` | an active `read` or `bash` tool |
| Typed `tool_call` events for other extensions | `extensions/types.ts` | name and input shape |
| HTML export rendering | `export-html/index.ts` | name |

This is a teaching point for module 05: a tool's name is part of its contract with the rest of the application.

## 5. How participants load their extensions

Pi already supports two ways:

- Flag: `pi -e education/exercises/01-read/read.ts` (`--extension`, repeatable).
- Discovery: put the file in the project's `.pi/extensions/` directory.

Each exercise directory contains a README and a starter extension (`starter.ts`) with the tool defined, its schema written and the registration done; participants implement `execute()`. Until they do, it returns an error result that says the tool is not implemented, so every starter loads and runs. See [exercises/README.md](../exercises/README.md).

Instructor solutions (`solution.ts` in each exercise directory) live on the `workshop-solutions` branch (decision 3), with `packages/coding-agent/test/suite/workshop-solutions.test.ts`.

## 6. Tests and examples to update

### Tests that exercise removed implementations (delete)

In `packages/coding-agent/test/`:

- `tools.test.ts`, `read-streaming.test.ts`, `read-line-range-display.test.ts`, `edit-tool-diff-before-write.test.ts`, `edit-tool-legacy-input.test.ts`, `edit-tool-no-full-redraw.test.ts`, `edit-diff-window.test.ts`, `grep-operations.test.ts`, `find-abort-before-spawn.test.ts`, `powershell-tool.test.ts`, `bash-close-hang-windows.test.ts`, `builtin-tool-strict-mode.test.ts`, `tool-system-prompt-contributions.test.ts`, `image-resize-callers.test.ts`, `output-pad.test.ts`, `block-images.test.ts`
- `suite/regressions/3302-find-path-glob.test.ts`, `3303-find-nested-gitignore.test.ts`, `6104-find-root-relativization.test.ts`, `12066-find-ancestor-glob.test.ts`, `5208-late-bash-output.test.ts`, `11613-bash-timeout-after-shell-exit.test.ts`

Each must be read before deleting. Some may test retained code (renderers, `edit-diff.ts`, the user shell) through a built-in tool, and those parts should be rewritten against a test tool instead of deleted.

### Tests that use built-in tools as fixtures (rewrite with a test tool)

- `agent-session-compaction.test.ts`, `agent-session-dynamic-tools.test.ts`, `compaction-extensions.test.ts`, `file-mutation-queue.test.ts`, `tool-execution-component.test.ts`, `suite/agent-session-bash-persistence.test.ts`, `utilities.ts`

### Tests that assert the default active tools (check and update)

- `default-tools-setting.test.ts`, `agent-session-branching.test.ts`, `plan-mode-extension.test.ts`, `system-prompt-updates.test.ts`, `tool-renderer-examples.test.ts`, `suite/agent-session-tool-orchestration.test.ts`

This list comes from a search for factory names and the default-name literal. `./test.sh` after the change is the full check.

### Examples

The five examples in 2.3 stop compiling. Deleted (decision 2).

## 7. Verification

1. `npm run check` passes with no errors, warnings or infos.
2. `./test.sh` passes.
3. New suite test (`test/suite/`, faux provider, no API keys):
   - a session with no extensions has no active tools, and the system prompt tool list is `(none)`;
   - a session with an inline extension that registers `read` has `read` active; a faux model call to `read` reaches the extension's `execute()`, and the tool result goes back into the next model request.
4. Each instructor solution passes a test of the same shape, so the solutions are known to work with the pinned revision.
5. Manual interactive check (tmux, per `.pi/skills/interactive-testing.md`):
   - `pi` starts, chat works with a real provider, `!ls` still runs;
   - `pi -e <solution>/read.ts`: a read call renders with the built-in `read` renderer;
   - all four solutions loaded together: the agent can read, edit and run a test in a sample project.

## 8. Decisions

Decided:

1. **Durable's tools and p2's coding-tools plugin: keep.** They are outside the workshop path and p2 depends on them. The learning map will point to them as a second, independent implementation to compare after the workshop.
2. **The five examples in 2.3: delete.** `ssh.ts`, `gondolin/`, `minimal-mode.ts`, `built-in-tool-renderer.ts`, `bash-spawn-hook.ts`, and any references to them in the examples README and tests.
3. **Instructor solutions: separate branch.** Participants work on `main`; solutions live on a branch (name to be chosen) that adds `education/solutions/`. The solution tests run on that branch.

Taken from the recommendations (reversible; say so to change):

4. **`createLocalBashOperations` stays public.** It is documented extension API used by `user_bash` handlers. The bash exercise states that the goal is to spawn the process yourself.
5. **`edit-diff.ts` stays.** The edit renderer uses it for previews; removing it means rewriting the renderer.
6. **Docs in `packages/coding-agent/docs/`:** one note at the top of each affected file instead of rewriting them, for the smaller upstream diff.

## Order of work

1. ~~Resolve the open decisions.~~ Done (section 8).
2. ~~Trim `core/tools/` and update `agent-session.ts`, `sdk.ts`, `index.ts`.~~ Done.
3. ~~Update tests and examples; add the verification suite test.~~ Done. Loadout tests register stand-ins for the removed tools through the extension API (`test/fixtures/stand-in-tools.ts`, inactive on registration like the removed built-ins); `test/suite/agent-session-workshop-tools.test.ts` covers the verification in section 7, item 3.
4. ~~`npm run check`, `./test.sh`.~~ Done. `packages/env` needs `cargo` to build its daemon and was not run where cargo is missing; no change touches it.
5. ~~Write the starter extensions and instructor solutions; test each solution.~~ Done; the bash solution is tested with a stand-in for `docker` where no Docker daemon runs.
6. Manual interactive check.
7. Update docs.
