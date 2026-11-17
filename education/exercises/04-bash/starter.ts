// Exercise 04: the bash tool. Lets the agent run commands, inside a Docker container.
//
// Needs Docker running and the image pulled once:  docker pull node:22-bookworm-slim
// Load it with the earlier tools, from the playground copy (see ../README.md):
//   ./pi-test.sh -e .../01-read/starter.ts -e .../02-write/starter.ts -e .../03-edit/starter.ts \
//     -e .../04-bash/starter.ts
// Then ask: "Run the tests and fix what fails."
//
// LEARN:
// A command is a child process: output arrives in chunks on stdout and stderr, it ends with an exit
// code, and it may never end at all. The tool turns that into one result the model can read, and a
// non-zero exit code is an error result the model should react to.
//
// SAFETY:
// The model writes the commands. They run in a throwaway container (`--rm`) meant to see only the
// working directory, mounted at /workspace, with no network. `dockerArgs` below builds that command
// line; change the isolation only on purpose. It is not a proven sandbox: see "Isolation checks" in
// README.md.

import { Type } from "typebox";
import { defineTool, type ExtensionAPI } from "@earendil-works/pi-coding-agent";

/** Image the commands run in. It must have bash. */
export const WORKSHOP_IMAGE = "node:22-bookworm-slim";

/** Arguments for `docker` that run `command` in a disposable container with only `workspace` mounted. Exported for the exercise tests. */
export function dockerArgs(command: string, workspace: string): string[] {
	// Run as the host user, so files the command creates in the workspace stay editable on the host.
	const user = process.getuid && process.getgid ? ["--user", `${process.getuid()}:${process.getgid()}`] : [];
	return [
		"run",
		"--rm",
		// An init process forwards the stop signal to the command, so killing `docker run` stops the command.
		"--init",
		"--network",
		"none",
		"--memory",
		"1g",
		"--pids-limit",
		"256",
		...user,
		"--env",
		"HOME=/tmp",
		"--volume",
		`${workspace}:/workspace`,
		"--workdir",
		"/workspace",
		WORKSHOP_IMAGE,
		"bash",
		"-c",
		command,
	];
}

const bashTool = defineTool({
	name: "bash",
	label: "bash",
	description:
		"Execute a bash command in the working directory, inside a container without network. Returns stdout and stderr combined. Optionally provide a timeout in seconds.",
	promptSnippet: "Execute bash commands (ls, grep, find, etc.)",
	parameters: Type.Object({
		command: Type.String({ description: "Bash command to execute" }),
		timeout: Type.Optional(Type.Number({ description: "Timeout in seconds (optional, no default timeout)" })),
	}),

	async execute(_toolCallId, params, _signal, _onUpdate, ctx) {
		// EXERCISE 1: Start the process: `spawn("docker", dockerArgs(params.command, ctx.cwd))` from
		// node:child_process. Spawning fails with code "ENOENT" when Docker is not installed; throw an
		// Error that says so.
		//
		// EXERCISE 2: Collect output. Append every chunk from `child.stdout` and `child.stderr` to one
		// buffer, in arrival order, the way a terminal shows them.
		//
		// EXERCISE 3: Wait for the "close" event, which gives the exit code. Return the output; when the
		// exit code is not 0, add "Command exited with code N" and set `isError: true`.
		//
		// EXERCISE 4: Stop runaway commands. Kill the process when `params.timeout` seconds pass, and
		// when `_signal` aborts (the user pressed Escape). Say in the result that the command was stopped.
		//
		// CHALLENGE: Stream output while the command runs: call `_onUpdate({ content, details: undefined })`
		// with the output so far, at most every 100 ms.
		//
		// CHALLENGE: Long output. Keep the last 2000 lines or 50 KB for the model (`truncateTail`,
		// exported by @earendil-works/pi-coding-agent) and say how much was left out.
		return {
			content: [
				{ type: "text", text: `bash is not implemented yet (asked to run ${params.command} in ${ctx.cwd}).` },
			],
			details: undefined,
			isError: true,
		};
	},
});

export default function (pi: ExtensionAPI) {
	pi.registerTool(bashTool);
}
