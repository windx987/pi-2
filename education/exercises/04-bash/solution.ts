// Solution for exercise 04: the bash tool. Lets the agent run commands, inside a Docker container. Instructor reference; participants get starter.ts.
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
// The model writes the commands. They run in a throwaway container (`--rm`) that sees only the
// working directory, mounted at /workspace, with no network. `dockerArgs` below builds that command
// line; change the isolation only on purpose.

import { type ChildProcess, spawn } from "node:child_process";
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

	async execute(_toolCallId, params, signal, _onUpdate, ctx) {
		if (signal?.aborted) throw new Error("Command aborted");
		const child = spawn("docker", dockerArgs(params.command, ctx.cwd), { stdio: ["ignore", "pipe", "pipe"] });
		let output = "";
		child.stdout.setEncoding("utf-8").on("data", (chunk: string) => {
			output += chunk;
		});
		child.stderr.setEncoding("utf-8").on("data", (chunk: string) => {
			output += chunk;
		});

		let stopped: string | undefined;
		const stop = (reason: string) => {
			stopped ??= reason;
			child.kill("SIGTERM");
		};
		const onAbort = () => stop("Command aborted");
		signal?.addEventListener("abort", onAbort, { once: true });
		const timer =
			params.timeout === undefined
				? undefined
				: setTimeout(() => stop(`Command timed out after ${params.timeout} seconds`), params.timeout * 1000);
		let exitCode: number | null;
		try {
			exitCode = await waitForExit(child);
		} finally {
			clearTimeout(timer);
			signal?.removeEventListener("abort", onAbort);
		}

		const text = output || "(no output)";
		if (stopped) throw new Error(`${text}\n\n${stopped}`);
		if (exitCode !== 0) {
			return {
				content: [{ type: "text", text: `${text}\n\nCommand exited with code ${exitCode}` }],
				details: undefined,
				isError: true,
			};
		}
		return { content: [{ type: "text", text }], details: undefined };
	},
});

/** The exit code once the process and its output streams close; null when a signal ended it. */
function waitForExit(child: ChildProcess): Promise<number | null> {
	return new Promise((resolve, reject) => {
		child.once("error", (error: NodeJS.ErrnoException) => {
			reject(
				error.code === "ENOENT"
					? new Error("Docker is not installed or not on PATH: the bash tool runs commands in a Docker container.")
					: error,
			);
		});
		child.once("close", (code) => resolve(code));
	});
}

export default function (pi: ExtensionAPI) {
	pi.registerTool(bashTool);
}
