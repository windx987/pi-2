// Exercise 03: the edit tool. Lets the agent change part of a file without rewriting all of it.
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

import { Type } from "typebox";
import { defineTool, type ExtensionAPI } from "@earendil-works/pi-coding-agent";

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
		// EXERCISE 1: Resolve `params.path` against `ctx.cwd` and read the file as UTF-8.
		//
		// EXERCISE 2: For each edit, find `oldText` in the ORIGINAL content (not in the result of the
		// previous edit). Throw an Error when it occurs zero times or more than once; include which
		// edit failed (edits[0], edits[1], ...) so the model can fix that one.
		//
		// EXERCISE 3: Reject overlapping edits, then apply all replacements. Apply from the end of the
		// file to the start, so earlier positions stay valid.
		//
		// EXERCISE 4: Write the new content and return a confirmation with details for the renderer:
		//   const { diff, firstChangedLine } = generateDiffString(original, updated);
		//   const patch = generateUnifiedPatch(params.path, original, updated);
		//   return { content: [{ type: "text", text: "..." }], details: { diff, patch, firstChangedLine } };
		// (`generateDiffString` and `generateUnifiedPatch` are exported by @earendil-works/pi-coding-agent.)
		//
		// CHALLENGE: Windows line endings. A file with CRLF line endings does not contain an oldText the
		// model wrote with LF. Match on LF-normalized text and write CRLF back.
		return {
			content: [{ type: "text", text: `edit is not implemented yet (asked for ${params.path} in ${ctx.cwd}).` }],
			details: undefined,
			isError: true,
		};
	},
});

export default function (pi: ExtensionAPI) {
	pi.registerTool(editTool);
}
