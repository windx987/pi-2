// Exercise 01: the read tool. Lets the agent look at files in its working directory.
//
// Load it:  ./pi-test.sh -e education/exercises/01-read/read.ts
// Then ask: "What is in package.json?"
//
// LEARN:
// A tool is plain data plus one function. `defineTool` describes it to the model (name, description,
// JSON Schema of the arguments) and `pi.registerTool` hands it to Pi. From there Pi does the rest:
// it declares the tool to the model, validates the model's arguments against `parameters`, calls
// `execute`, and sends what you return back to the model as the tool result.
//
// TRACE:
// packages/coding-agent/src/core/agent-session.ts  _refreshToolRegistry()  (registration)
// packages/agent/src/agent-loop.ts                                         (dispatch and results)

import { Type } from "typebox";
import { defineTool, type ExtensionAPI } from "@earendil-works/pi-coding-agent";

const readTool = defineTool({
	// The name is part of the contract: Pi's TUI renderer, compaction and the skills prompt look for "read".
	name: "read",
	label: "read",
	description:
		"Read the contents of a text file. Use offset and limit to read part of a large file; offset is the first line to read, starting at 1.",
	promptSnippet: "Read file contents",
	promptGuidelines: ["Use read to examine files instead of cat or sed."],
	parameters: Type.Object({
		path: Type.String({ description: "Path to the file, relative to the working directory or absolute" }),
		offset: Type.Optional(Type.Number({ description: "Line number to start reading from (1-indexed)" })),
		limit: Type.Optional(Type.Number({ description: "Maximum number of lines to read" })),
	}),

	async execute(_toolCallId, params, _signal, _onUpdate, ctx) {
		// EXERCISE 1: Resolve `params.path` against `ctx.cwd` (node:path `resolve`), so relative paths
		// mean "relative to the directory the agent works in".
		//
		// EXERCISE 2: Read the file as UTF-8 text (node:fs/promises `readFile`).
		//
		// EXERCISE 3: Apply `params.offset` and `params.limit`. Split into lines, keep the selected ones,
		// and when lines remain after them, end the text with a note such as
		// "[120 more lines. Use offset=201 to continue.]" so the model knows how to read on.
		//
		// EXERCISE 4: Errors. Throw an `Error` for a missing file or an offset past the end of the file.
		// Pi turns a thrown error into an error result; write the message for the model, which reads it.
		//
		// Return the text as: { content: [{ type: "text", text }], details: undefined }
		//
		// CHALLENGE: Large files. Cap the output (for example 2000 lines or 50 KB) and say so in the text.
		// See `truncateHead` exported by @earendil-works/pi-coding-agent.
		return {
			content: [{ type: "text", text: `read is not implemented yet (asked for ${params.path} in ${ctx.cwd}).` }],
			details: undefined,
			isError: true,
		};
	},
});

export default function (pi: ExtensionAPI) {
	pi.registerTool(readTool);
}
