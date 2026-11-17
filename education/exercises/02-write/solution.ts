// Solution for exercise 02: the write tool. Lets the agent create files and replace them whole. Instructor reference; participants get starter.ts.
//
// Load it with the read tool:
//   ./pi-test.sh -e education/exercises/01-read/starter.ts -e education/exercises/02-write/starter.ts
// Then ask: "Create notes/todo.md with three items."
//
// LEARN:
// The model fills `parameters` as JSON. Pi validates that JSON against the schema before `execute`
// runs, so `params` here always has a string `path` and a string `content`: you check only what the
// schema cannot say, such as where the file may be written.
//
// SAFETY:
// Whatever path the model sends is written. Decide which directories the agent may write to.

import { mkdir, writeFile } from "node:fs/promises";
import { dirname, isAbsolute, relative, resolve, sep } from "node:path";
import { Type } from "typebox";
import { defineTool, type ExtensionAPI } from "@earendil-works/pi-coding-agent";

const writeTool = defineTool({
	name: "write",
	label: "write",
	description:
		"Write content to a file. Creates the file if it does not exist, overwrites it if it does, and creates parent directories.",
	promptSnippet: "Create or overwrite files",
	promptGuidelines: ["Use write only for new files or complete rewrites."],
	parameters: Type.Object({
		path: Type.String({ description: "Path to the file, relative to the working directory or absolute" }),
		content: Type.String({ description: "Content to write to the file" }),
	}),

	async execute(_toolCallId, params, _signal, _onUpdate, ctx) {
		const absolutePath = resolve(ctx.cwd, params.path);
		const fromCwd = relative(ctx.cwd, absolutePath);
		if (fromCwd === ".." || fromCwd.startsWith(`..${sep}`) || isAbsolute(fromCwd)) {
			throw new Error(`Refusing to write ${params.path}: only files inside the working directory may be written.`);
		}
		await mkdir(dirname(absolutePath), { recursive: true });
		await writeFile(absolutePath, params.content, "utf-8");
		return {
			content: [{ type: "text", text: `Wrote ${Buffer.byteLength(params.content)} bytes to ${params.path}` }],
			details: undefined,
		};
	},
});

export default function (pi: ExtensionAPI) {
	pi.registerTool(writeTool);
}
