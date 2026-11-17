import { type Static, Type } from "typebox";
import type { TruncationResult } from "./truncate.ts";

const lsSchema = Type.Object({
	path: Type.Optional(Type.String({ description: "Directory to list (default: current directory)" })),
	limit: Type.Optional(Type.Number({ description: "Maximum number of entries to return (default: 500)" })),
});

export type LsToolInput = Static<typeof lsSchema>;

export interface LsToolDetails {
	truncation?: TruncationResult;
	entryLimitReached?: number;
}
