// Exercise 02: the write tool. Lets the agent create files and replace them whole.
//
// Load it with the read tool:
//   ./pi-test.sh -e education/exercises/01-read/read.ts -e education/exercises/02-write/write.ts
// Then ask: "Create notes/todo.md with three items."
//
// LEARN:
// The model fills `parameters` as JSON. Pi validates that JSON against the schema before `execute`
// runs, so `params` here always has a string `path` and a string `content`: you check only what the
// schema cannot say, such as where the file may be written.
//
// SAFETY:
// Whatever path the model sends is written. Decide which directories the agent may write to.

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
		// EXERCISE 1: Resolve `params.path` against `ctx.cwd`.
		//
		// EXERCISE 2: Validation. Refuse paths outside `ctx.cwd` (node:path `relative`: a result that
		// starts with ".." or is absolute leaves the directory). Throw an Error that says why.
		//
		// EXERCISE 3: Create the parent directories (`mkdir` with `recursive: true`), then write the
		// content as UTF-8 (`writeFile`).
		//
		// EXERCISE 4: Return a short confirmation, such as "Wrote 120 bytes to notes/todo.md". The model
		// does not see the file unless it reads it, so say what happened.
		//
		// CHALLENGE: Two tool calls can run at the same time. Wrap the write in `withFileMutationQueue`
		// (exported by @earendil-works/pi-coding-agent) so writes and edits to one file do not interleave.
		return {
			content: [{ type: "text", text: `write is not implemented yet (asked for ${params.path} in ${ctx.cwd}).` }],
			details: undefined,
			isError: true,
		};
	},
});

export default function (pi: ExtensionAPI) {
	pi.registerTool(writeTool);
}
