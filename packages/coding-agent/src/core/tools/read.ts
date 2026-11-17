import { type Static, Type } from "typebox";
import type { TruncationResult } from "./truncate.ts";

const readSchema = Type.Object({
	path: Type.String({ description: "Path to the file to read (relative or absolute)" }),
	offset: Type.Optional(Type.Number({ description: "Line number to start reading from (1-indexed)" })),
	limit: Type.Optional(Type.Number({ description: "Maximum number of lines to read" })),
});

export type ReadToolInput = Static<typeof readSchema>;

export interface ReadToolDetails {
	truncation?: TruncationResult;
	/**
	 * Id of the model that was selected when the image was read, if it has no image input. Shown to the user only:
	 * the model gets pi-ai's placeholder per request, so the stored result stays right after a model switch.
	 */
	imageUnsupportedByModel?: string;
}
