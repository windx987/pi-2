// Stand-ins for the coding tools the workshop edition removed. Tests that exercise tool loadouts
// (defaultTools, --tools, --exclude-tools, resume) register them through the extension API, the way a
// participant's tools arrive. They are never default tools: a session only has them when a test loads
// this extension. They register inactive (`defaultActive: false`), so like the removed built-in tools
// they are active only when the default selection, `defaultTools` or `--tools` names them.

import { Type } from "typebox";
import type { ExtensionFactory, ToolDefinition } from "../../src/core/extensions/types.ts";

/** Names of the stand-in tools, the same names the removed built-in tools had. */
export const STAND_IN_TOOL_NAMES = ["read", "bash", "powershell", "edit", "write", "grep", "find", "ls"] as const;

const snippets: Record<(typeof STAND_IN_TOOL_NAMES)[number], string> = {
	read: "Read file contents",
	bash: "Execute bash commands (ls, grep, find, etc.)",
	powershell: "Execute PowerShell commands",
	edit: "Make precise file edits with exact text replacement",
	write: "Create or overwrite files",
	grep: "Search file contents for patterns",
	find: "Find files by glob pattern",
	ls: "List directory contents",
};

// The removed read tool's guideline: tests check that guidelines reach the system prompt and codemode.
const guidelines: Partial<Record<(typeof STAND_IN_TOOL_NAMES)[number], string[]>> = {
	read: ["Use read to examine files instead of cat or sed."],
};

/** A stand-in tool that echoes its name. */
export function createStandInTool(name: (typeof STAND_IN_TOOL_NAMES)[number]): ToolDefinition {
	return {
		name,
		label: name,
		description: `Stand-in ${name} tool`,
		promptSnippet: snippets[name],
		promptGuidelines: guidelines[name],
		parameters: Type.Object({ path: Type.Optional(Type.String()), command: Type.Optional(Type.String()) }),
		defaultActive: false,
		execute: async () => ({ content: [{ type: "text", text: `${name} ok` }], details: undefined }),
	};
}

/** Extension that registers every stand-in tool. */
export const standInToolsExtension: ExtensionFactory = (pi) => {
	for (const name of STAND_IN_TOOL_NAMES) pi.registerTool(createStandInTool(name));
};
