import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fauxAssistantMessage, fauxToolCall } from "@earendil-works/pi-ai";
import { afterEach, describe, expect, it } from "vitest";
import { dockerArgs } from "../../../../education/exercises/04-bash/bash.ts";
import { DefaultResourceLoader } from "../../src/core/resource-loader.ts";
import { SettingsManager } from "../../src/core/settings-manager.ts";
import { createHarness, getToolResult, type Harness } from "./harness.ts";

const exercisesDir = join(import.meta.dirname, "../../../../education/exercises");

const starters = [
	{ name: "read", path: "01-read/read.ts", args: { path: "math.js" } },
	{ name: "write", path: "02-write/write.ts", args: { path: "notes.md", content: "hi" } },
	{ name: "edit", path: "03-edit/edit.ts", args: { path: "math.js", edits: [{ oldText: "a", newText: "b" }] } },
	{ name: "bash", path: "04-bash/bash.ts", args: { command: "npm test" } },
] as const;

// The starters load through Pi's extension loader, as `pi -e` loads them, and their tools go through
// the normal tool lifecycle before a participant implements anything.
describe("workshop exercise starters", () => {
	const harnesses: Harness[] = [];
	const dirs: string[] = [];

	afterEach(() => {
		while (harnesses.length > 0) harnesses.pop()?.cleanup();
		for (const dir of dirs.splice(0)) rmSync(dir, { recursive: true, force: true });
	});

	async function loadStarters(paths: string[]): Promise<Harness> {
		const cwd = mkdtempSync(join(tmpdir(), "pi-workshop-starters-"));
		dirs.push(cwd);
		const resourceLoader = new DefaultResourceLoader({
			cwd,
			agentDir: join(cwd, "agent"),
			settingsManager: SettingsManager.inMemory(),
			additionalExtensionPaths: paths.map((path) => join(exercisesDir, path)),
		});
		await resourceLoader.reload();
		expect(resourceLoader.getExtensions().errors).toEqual([]);
		const harness = await createHarness({ resourceLoader });
		harnesses.push(harness);
		return harness;
	}

	it.each(starters)("registers $name and returns its not-implemented error result", async ({ name, path, args }) => {
		const harness = await loadStarters([path]);
		expect(harness.session.getActiveToolNames()).toEqual([name]);
		harness.setResponses([
			fauxAssistantMessage([fauxToolCall(name, args)], { stopReason: "toolUse" }),
			fauxAssistantMessage("done"),
		]);

		await harness.session.prompt("go");

		const result = getToolResult(harness, name);
		expect(result.isError).toBe(true);
		expect(result.content).toEqual([
			{ type: "text", text: expect.stringContaining(`${name} is not implemented yet`) },
		]);
	});

	it("loads all four starters together", async () => {
		const harness = await loadStarters(starters.map((starter) => starter.path));
		expect(harness.session.getActiveToolNames().sort()).toEqual(["bash", "edit", "read", "write"]);
		expect(harness.session.systemPrompt).toContain("- read: Read file contents");
	});

	it("keeps the edit tool's self-rendered frame", async () => {
		const harness = await loadStarters(["03-edit/edit.ts"]);
		expect(harness.session.getToolDefinition("edit")?.renderShell).toBe("self");
	});

	it("runs bash commands in a disposable container that sees only the workspace", () => {
		const args = dockerArgs("npm test", "/tmp/pi-workshop");
		expect(args.slice(0, 2)).toEqual(["run", "--rm"]);
		expect(args).toEqual(expect.arrayContaining(["--network", "none", "--volume", "/tmp/pi-workshop:/workspace"]));
		expect(args.slice(-3)).toEqual(["bash", "-c", "npm test"]);
	});
});
