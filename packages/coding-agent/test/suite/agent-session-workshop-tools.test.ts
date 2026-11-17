import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fauxAssistantMessage, fauxToolCall, getCurrentTools, type TranscriptContext } from "@earendil-works/pi-ai";
import { Type } from "typebox";
import { afterEach, describe, expect, it } from "vitest";
import { defineTool, type ExtensionFactory } from "../../src/core/extensions/types.ts";
import { DefaultResourceLoader } from "../../src/core/resource-loader.ts";
import { SessionManager } from "../../src/core/session-manager.ts";
import { SettingsManager } from "../../src/core/settings-manager.ts";
import { createHarness, getToolResult, type Harness } from "./harness.ts";

// The workshop edition ships no coding tools: a fresh session declares none, and the tools a participant
// registers through an extension go through Pi's normal loadout, dispatch and result feedback.
describe("workshop edition tools", () => {
	const harnesses: Harness[] = [];

	afterEach(() => {
		while (harnesses.length > 0) harnesses.pop()?.cleanup();
	});

	const calls: Array<{ path: string }> = [];

	// A participant's read tool, written the way the exercises ask: defineTool plus pi.registerTool.
	const participantTools: ExtensionFactory = (pi) => {
		pi.registerTool(
			defineTool({
				name: "read",
				label: "Read",
				description: "Read a file",
				promptSnippet: "Read file contents",
				parameters: Type.Object({ path: Type.String() }),
				execute: async (_toolCallId, params) => {
					calls.push(params);
					return { content: [{ type: "text", text: `contents of ${params.path}` }], details: undefined };
				},
			}),
		);
		pi.registerTool(
			defineTool({
				name: "write",
				label: "Write",
				description: "Write a file",
				promptSnippet: "Create or overwrite files",
				parameters: Type.Object({ path: Type.String(), content: Type.String() }),
				execute: async () => ({ content: [{ type: "text", text: "written" }], details: undefined }),
			}),
		);
	};

	function recordTools(requests: string[][]) {
		return (context: TranscriptContext) => {
			requests.push(getCurrentTools(context.messages).map((tool) => tool.name));
			return fauxAssistantMessage("ok");
		};
	}

	it("declares no tools to the model in a fresh session without extensions", async () => {
		// The default resource loader, as `pi` uses it, with its built-in extensions and no user extensions.
		const cwd = mkdtempSync(join(tmpdir(), "pi-workshop-tools-"));
		const resourceLoader = new DefaultResourceLoader({
			cwd,
			agentDir: join(cwd, "agent"),
			settingsManager: SettingsManager.inMemory(),
		});
		await resourceLoader.reload();
		const harness = await createHarness({ resourceLoader });
		harnesses.push(harness);

		const requests: string[][] = [];
		harness.setResponses([recordTools(requests)]);
		await harness.session.prompt("hello");

		expect(harness.session.getActiveToolNames()).toEqual([]);
		expect(harness.session.systemPrompt).toContain("<tools>\n(none)\n");
		expect(requests).toEqual([[]]);
		rmSync(cwd, { recursive: true, force: true });
	});

	it("declares, dispatches and feeds back the results of tools a participant registers", async () => {
		calls.length = 0;
		const harness = await createHarness({ extensionFactories: [participantTools] });
		harnesses.push(harness);
		const requests: string[][] = [];
		let resultInNextRequest = false;
		harness.setResponses([
			(context) => {
				requests.push(getCurrentTools(context.messages).map((tool) => tool.name));
				return fauxAssistantMessage([fauxToolCall("read", { path: "notes.txt" })], { stopReason: "toolUse" });
			},
			(context) => {
				resultInNextRequest = context.messages.some(
					(message) => message.role === "toolResult" && message.toolName === "read",
				);
				return fauxAssistantMessage("done");
			},
		]);

		await harness.session.prompt("read notes.txt");

		expect(harness.session.getActiveToolNames()).toEqual(["read", "write"]);
		expect(harness.session.systemPrompt).toContain("- read: Read file contents");
		expect(requests[0]).toEqual(["read", "write"]);
		expect(calls).toEqual([{ path: "notes.txt" }]);
		expect(getToolResult(harness, "read").content).toEqual([{ type: "text", text: "contents of notes.txt" }]);
		expect(resultInNextRequest).toBe(true);
	});

	it("applies --tools and --exclude-tools to participant tools", async () => {
		const allowed = await createHarness({ extensionFactories: [participantTools], allowedToolNames: ["read"] });
		harnesses.push(allowed);
		expect(allowed.session.getActiveToolNames()).toEqual(["read"]);

		const excluded = await createHarness({ extensionFactories: [participantTools], excludedToolNames: ["read"] });
		harnesses.push(excluded);
		expect(excluded.session.getActiveToolNames()).toEqual(["write"]);
		expect(excluded.session.getAllTools().map((tool) => tool.name)).not.toContain("read");
	});

	it("restores the participant tool loadout on resume", async () => {
		const sessionManager = SessionManager.inMemory();
		const first = await createHarness({ extensionFactories: [participantTools], sessionManager });
		harnesses.push(first);
		first.setResponses([fauxAssistantMessage("ok"), fauxAssistantMessage("ok")]);
		await first.session.prompt("hello");
		// The transcript records write being removed; a tool it never mentioned would be active again (#11062).
		first.session.setActiveToolsByName(["read"]);
		await first.session.prompt("again");

		const resumed = await createHarness({ extensionFactories: [participantTools], sessionManager });
		harnesses.push(resumed);
		expect(resumed.session.getActiveToolNames()).toEqual(["read"]);
	});
});
