// Solution for exercise 01: the read tool. Lets the agent look at files in its working directory. Instructor reference; participants get read.ts.
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

import { readFile } from "node:fs/promises";
import { resolve } from "node:path";
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
		const text = await readText(resolve(ctx.cwd, params.path), params.path);
		const lines = text.split("\n");
		const start = Math.max(0, (params.offset ?? 1) - 1);
		if (start >= lines.length) {
			throw new Error(`Offset ${params.offset} is beyond the end of ${params.path} (${lines.length} lines).`);
		}
		const end = params.limit === undefined ? lines.length : Math.min(lines.length, start + params.limit);
		let output = lines.slice(start, end).join("\n");
		if (end < lines.length) {
			output += `\n\n[${lines.length - end} more lines. Use offset=${end + 1} to continue.]`;
		}
		return { content: [{ type: "text", text: output }], details: undefined };
	},
});

/** The file's text; a missing file is an error the model can act on. */
async function readText(absolutePath: string, requestedPath: string): Promise<string> {
	try {
		return await readFile(absolutePath, "utf-8");
	} catch (error) {
		if ((error as NodeJS.ErrnoException).code === "ENOENT") throw new Error(`File not found: ${requestedPath}`);
		throw error;
	}
}

export default function (pi: ExtensionAPI) {
	pi.registerTool(readTool);
}
