# 04: Bash

## Learning objectives

- Run a child process and collect its output streams.
- Map an exit code to a result the model reacts to.
- Bound what a command can do: time limits, cancellation, isolation.

## Concept

With `bash` the agent can do anything a shell can, so where the shell runs matters. This exercise runs every command in a new Docker container that is meant to see only the working directory (mounted at `/workspace`), to have no network, and to be removed when the command ends. `dockerArgs` in `starter.ts` builds that command line for you; your job is the process handling around it.

The container reduces what a command can reach; it is not a proven sandbox. Run the checks in [Isolation checks](#isolation-checks) on your machine before relying on it.

A command result has three parts the model needs: the output (stdout and stderr in the order they arrived), the exit code, and whether it was stopped. A non-zero exit code is not a tool failure, but the model must notice it, so it is reported as an error result together with the output.

## Execution flow

1. The model calls `bash({ "command": "npm test" })`.
2. `execute` spawns `docker run ... bash -c "npm test"` with the working directory mounted.
3. Output chunks arrive on stdout and stderr; the tool collects them, and optionally streams them to the TUI with `onUpdate`.
4. The process closes with an exit code. The tool returns the output, marked as an error when the code is not 0.
5. A timeout or Escape (`signal`) kills the process, and the result says the command was stopped.

## Source code walkthrough

| File | What to look at |
|---|---|
| `packages/coding-agent/src/core/tools/bash.ts` | `createLocalShellOperations`: Pi's process handling for the user `!` shell (timeouts, process trees, exit codes from signals) |
| `packages/coding-agent/src/core/tools/renderers/bash.ts` | How the TUI shows commands, output, elapsed time |
| `packages/coding-agent/src/core/bash-executor.ts` | Output sanitizing and spill-to-file for long output |

## Hands-on exercise

Start Docker and pull the image once: `docker pull node:22-bookworm-slim`. Implement `execute()` in `starter.ts` (EXERCISE 1 to 4). Load all four tools from the playground copy and ask:

- "Run the tests." The result shows a failing test and exit code 1.
- "Fix the failing test." The agent reads `math.js`, edits it, and runs the tests again.
- "Run `sleep 30` with a 2 second timeout."
- "Run `curl https://example.com`." It fails: the container has no network.

## Expected result

- The TUI shows `$ npm test`, the output, and how long it took.
- Failing commands come back as error results with their output and exit code, and the agent reacts to them.
- The timeout stops the command; Escape stops a running command.

## Isolation checks

Status: not yet verified with a running Docker daemon. Each check below is a command to ask the agent to run, with the result that shows the isolation holds.

| Check | Command | Expected |
|---|---|---|
| No network | `curl -sS https://example.com` or `node -e "fetch('https://example.com')"` | Fails to resolve or connect |
| No host files outside the workspace | `ls /Users /home; cat /etc/hostname` | No host home directories; the hostname is the container's |
| Memory limit | `node -e "const a=[]; for(;;) a.push(Buffer.alloc(1e8))"` | Killed (exit code 137) at about 1 GB |
| Process limit | `for i in $(seq 400); do sleep 60 & done; wait` | Fails after about 256 processes |
| Timeout stops the container | `sleep 300` with `timeout: 2`, then `docker ps` on the host | No container left running |
| Cleanup after errors | a failing command, then `docker ps -a` on the host | No leftover container (`--rm`) |
| No escape through symlinks | `ln -s / host-root && ls host-root/` | Lists the container's root, not the host's |

SAFETY: the symlink check covers commands. Your `read`, `write` and `edit` tools run on the host: a symlink in the workspace that points outside it makes them reach the host. Resolve paths with `realpath` before the containment check if that matters for your setup.

## Further exploration

- The original tool: `git show cead615b4:packages/coding-agent/src/core/tools/bash.ts`.
- SAFETY: the isolation depends on the mount. Mounting a home directory or the Docker socket gives the agent the host back.
- CHALLENGE in `starter.ts`: streaming updates and output truncation.
