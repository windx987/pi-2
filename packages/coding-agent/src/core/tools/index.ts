// The built-in coding tools' contract: input and details types, keyed by the tool names Pi renders.
// The implementations were removed in the workshop edition; participants register their own tools
// with these names through extensions (see education/architecture/tool-removal.md).

export {
	type BashOperations,
	type BashToolDetails,
	type BashToolInput,
	createLocalBashOperations,
} from "./bash.ts";
export type { EditToolDetails, EditToolInput } from "./edit.ts";
export { withFileMutationQueue } from "./file-mutation-queue.ts";
export type { FindToolDetails, FindToolInput } from "./find.ts";
export type { GrepToolDetails, GrepToolInput } from "./grep.ts";
export type { LsToolDetails, LsToolInput } from "./ls.ts";
export {
	createLocalPowerShellOperations,
	type PowerShellOperations,
	type PowerShellToolDetails,
	type PowerShellToolInput,
} from "./powershell.ts";
export type { ReadToolDetails, ReadToolInput } from "./read.ts";
export {
	DEFAULT_MAX_BYTES,
	DEFAULT_MAX_LINES,
	formatSize,
	type TruncationOptions,
	type TruncationResult,
	truncateHead,
	truncateLine,
	truncateTail,
} from "./truncate.ts";
export type { WriteToolInput } from "./write.ts";

import type { AgentTool } from "@earendil-works/pi-agent-core";

export type Tool = AgentTool<any>;
export type ToolName = "read" | "bash" | "powershell" | "edit" | "write" | "grep" | "find" | "ls";
