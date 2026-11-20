// Solution for exercise 03: the edit tool. Lets the agent change part of a file without rewriting all of it. Instructor reference; participants get edit.ts.
//
// Load it with the earlier tools:
//   ./pi-test.sh -e education/exercises/01-read/read.ts -e education/exercises/02-write/write.ts \
//     -e education/exercises/03-edit/edit.ts
// Then ask: "Rename the function add to sum in math.js."
//
// LEARN:
// The model never sees line numbers it can trust, so it names the text to replace. That only works
// when the text matches exactly once: zero matches means the model's view of the file is stale, two
// means the edit is ambiguous. Both must be errors, never guesses.
//
// The arguments and `details` keep the shape of Pi's original edit tool, so Pi's built-in edit
// renderer previews the diff while the call streams and shows it in the result.

import { readFile, writeFile } from "node:fs/promises";
import { resolve } from "node:path";
import { Type } from "typebox";
import {
	defineTool,
	type ExtensionAPI,
	generateDiffString,
	generateUnifiedPatch,
} from "@earendil-works/pi-coding-agent";

const editParameters = Type.Object({
	path: Type.String({ description: "Path to the file, relative to the working directory or absolute" }),
	edits: Type.Array(
		Type.Object({
			oldText: Type.String({ description: "Exact text to replace; must occur once in the original file" }),
			newText: Type.String({ description: "Replacement text" }),
		}),
		{ description: "One or more replacements, each matched against the original file" },
	),
});

const editTool = defineTool({
	name: "edit",
	label: "edit",
	description:
		"Edit a file with exact text replacements. Each edits[].oldText must match exactly one place in the original file; edits must not overlap.",
	promptSnippet: "Make precise file edits with exact text replacement, including multiple disjoint edits in one call",
	promptGuidelines: ["Use edit for targeted changes. Batch changes to one file in a single call."],
	parameters: editParameters,
	// The edit renderer draws its own frame around the diff, as the original edit tool did.
	renderShell: "self",

	async execute(_toolCallId, params, _signal, _onUpdate, ctx) {
		const absolutePath = resolve(ctx.cwd, params.path);
		const original = await readOriginal(absolutePath, params.path);
		const matches = findMatches(original, params.edits, params.path);
		let updated = original;
		// From the end of the file to the start, so the earlier matches keep their positions.
		for (const match of matches.toReversed()) {
			updated = updated.slice(0, match.start) + match.newText + updated.slice(match.end);
		}
		await writeFile(absolutePath, updated, "utf-8");
		const { diff, firstChangedLine } = generateDiffString(original, updated);
		return {
			content: [{ type: "text", text: `Applied ${matches.length} edit(s) to ${params.path}` }],
			details: { diff, patch: generateUnifiedPatch(params.path, original, updated), firstChangedLine },
		};
	},
});

/** The file's text; a missing file is an error the model can act on. */
async function readOriginal(absolutePath: string, requestedPath: string): Promise<string> {
	try {
		return await readFile(absolutePath, "utf-8");
	} catch (error) {
		if ((error as NodeJS.ErrnoException).code === "ENOENT") throw new Error(`File not found: ${requestedPath}`);
		throw error;
	}
}

/** Where each edit applies in `original`, sorted by position; throws for a missing, repeated or overlapping match. */
function findMatches(
	original: string,
	edits: Array<{ oldText: string; newText: string }>,
	path: string,
): Array<{ index: number; start: number; end: number; newText: string }> {
	if (edits.length === 0) throw new Error("edits is empty: give at least one replacement.");
	const matches = edits.map((edit, index) => {
		const start = edit.oldText === "" ? -1 : original.indexOf(edit.oldText);
		if (start === -1) {
			throw new Error(`edits[${index}].oldText was not found in ${path}. Read the file again and copy the text exactly.`);
		}
		if (original.indexOf(edit.oldText, start + 1) !== -1) {
			throw new Error(
				`edits[${index}].oldText occurs more than once in ${path}. Include more surrounding text to make it unique.`,
			);
		}
		return { index, start, end: start + edit.oldText.length, newText: edit.newText };
	});
	matches.sort((a, b) => a.start - b.start);
	for (let i = 1; i < matches.length; i++) {
		if (matches[i].start < matches[i - 1].end) {
			throw new Error(`edits[${matches[i - 1].index}] and edits[${matches[i].index}] overlap. Merge them into one edit.`);
		}
	}
	return matches;
}

export default function (pi: ExtensionAPI) {
	pi.registerTool(editTool);
}
