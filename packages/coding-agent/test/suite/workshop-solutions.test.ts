import { chmodSync, cpSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fauxAssistantMessage, fauxToolCall, type JsonObject } from "@earendil-works/pi-ai";
import type { TUI } from "@earendil-works/pi-tui";
import { afterEach, beforeAll, describe, expect, it } from "vitest";
import { DefaultResourceLoader } from "../../src/core/resource-loader.ts";
import { SettingsManager } from "../../src/core/settings-manager.ts";
import { editRenderers } from "../../src/core/tools/renderers/edit.ts";
import { withBuiltInRenderers } from "../../src/core/tools/renderers/index.ts";
import { ToolExecutionComponent } from "../../src/modes/interactive/components/tool-execution.ts";
import { initTheme } from "../../src/modes/interactive/theme/theme.ts";
import { createHarness, type Harness } from "./harness.ts";

const educationDir = join(import.meta.dirname, "../../../../education");
const solutions = ["01-read", "02-write", "03-edit", "04-bash"].map((name) =>
	join(educationDir, "exercises", name, "solution.ts"),
);

// Stands in for Docker where no daemon runs: executes the `bash -c` command on the host, in the
// directory `--volume` mounts. It checks the tool's process handling, not the container.
const FAKE_DOCKER = `#!/usr/bin/env bash
while [ "$#" -gt 0 ]; do
	case "$1" in
		--volume) workspace="\${2%%:*}"; shift 2 ;;
		-c)
			# Like docker stopping the container: a stop signal ends the command and the processes it started.
			cd "$workspace" || exit 125
			bash -c "$2" &
			pid=$!
			trap 'pkill -TERM -P "$pid"; kill -TERM "$pid"' TERM
			wait "$pid"
			exit $? ;;
		*) shift ;;
	esac
done
`;

// The instructor solutions, loaded as `pi -e` loads them, complete each tool's lifecycle: the model
// calls the tool, the solution does the work, and the result goes back to the model.
describe("workshop exercise solutions", () => {
	const harnesses: Harness[] = [];
	const dirs: string[] = [];
	const originalPath = process.env.PATH;

	beforeAll(() => {
		initTheme("dark");
	});

	afterEach(() => {
		process.env.PATH = originalPath;
		while (harnesses.length > 0) harnesses.pop()?.cleanup();
		for (const dir of dirs.splice(0)) rmSync(dir, { recursive: true, force: true });
	});

	async function setup(): Promise<{ harness: Harness; workspace: string }> {
		const root = mkdtempSync(join(tmpdir(), "pi-workshop-solutions-"));
		dirs.push(root);
		const bin = join(root, "bin");
		mkdirSync(bin);
		writeFileSync(join(bin, "docker"), FAKE_DOCKER);
		chmodSync(join(bin, "docker"), 0o755);
		process.env.PATH = `${bin}:${originalPath}`;

		const resourceLoader = new DefaultResourceLoader({
			cwd: root,
			agentDir: join(root, "agent"),
			settingsManager: SettingsManager.inMemory(),
			additionalExtensionPaths: solutions,
		});
		await resourceLoader.reload();
		expect(resourceLoader.getExtensions().errors).toEqual([]);
		const harness = await createHarness({ resourceLoader });
		harnesses.push(harness);
		// The session works in the harness's directory: the playground copy goes there.
		cpSync(join(educationDir, "playground"), harness.tempDir, { recursive: true });
		return { harness, workspace: harness.tempDir };
	}

	/** Run one model turn that calls `name` with `args`; returns the tool result's text and error flag. */
	async function call(harness: Harness, name: string, args: JsonObject) {
		harness.setResponses([
			fauxAssistantMessage([fauxToolCall(name, args)], { stopReason: "toolUse" }),
			fauxAssistantMessage("done"),
		]);
		await harness.session.prompt(`call ${name}`);
		const result = harness.session.messages.filter((message) => message.role === "toolResult").at(-1);
		if (result?.role !== "toolResult") throw new Error(`no result for ${name}`);
		const text = result.content.map((block) => (block.type === "text" ? block.text : "")).join("");
		return { text, isError: result.isError, details: result.details };
	}

	it("reads, writes, edits and runs commands in the workspace", async () => {
		const { harness, workspace } = await setup();
		expect(harness.session.getActiveToolNames().sort()).toEqual(["bash", "edit", "read", "write"]);

		const read = await call(harness, "read", { path: "math.js", offset: 7, limit: 2 });
		expect(read).toMatchObject({ isError: false });
		expect(read.text).toContain("export function average(values) {");
		expect(read.text).toContain("more lines. Use offset=9 to continue.");

		expect((await call(harness, "read", { path: "missing.js" })).text).toContain("File not found: missing.js");

		const written = await call(harness, "write", { path: "notes/todo.md", content: "- fix average\n" });
		expect(written.text).toBe("Wrote 14 bytes to notes/todo.md");
		expect(readFileSync(join(workspace, "notes/todo.md"), "utf-8")).toBe("- fix average\n");
		const outside = await call(harness, "write", { path: "../outside.txt", content: "x" });
		expect(outside).toMatchObject({ isError: true });
		expect(outside.text).toContain("only files inside the working directory");

		const failing = await call(harness, "bash", { command: "node --test" });
		expect(failing.isError).toBe(true);
		expect(failing.text).toContain("Command exited with code 1");

		const fixed = await call(harness, "edit", {
			path: "math.js",
			edits: [{ oldText: "values.length - 1", newText: "values.length" }],
		});
		expect(fixed).toMatchObject({ isError: false, text: "Applied 1 edit(s) to math.js" });
		expect(fixed.details).toMatchObject({ diff: expect.stringContaining("values.length"), firstChangedLine: 10 });

		const passing = await call(harness, "bash", { command: "node --test" });
		expect(passing.isError).toBe(false);
		expect(passing.text).toContain("pass 2");
	});

	it("refuses edits that do not match exactly once or overlap", async () => {
		const { harness } = await setup();
		expect(
			(await call(harness, "edit", { path: "math.js", edits: [{ oldText: "nope", newText: "x" }] })).text,
		).toContain("edits[0].oldText was not found");
		expect(
			(await call(harness, "edit", { path: "math.js", edits: [{ oldText: "return", newText: "x" }] })).text,
		).toContain("occurs more than once");
		const overlap = await call(harness, "edit", {
			path: "math.js",
			edits: [
				{ oldText: "export function add(a, b)", newText: "x" },
				{ oldText: "add(a, b) {", newText: "y" },
			],
		});
		expect(overlap.text).toContain("overlap");
	});

	it("stops commands at their timeout", async () => {
		const { harness } = await setup();
		const startedAt = Date.now();
		const result = await call(harness, "bash", { command: "echo started; sleep 30", timeout: 1 });
		expect(result).toMatchObject({ isError: true });
		expect(result.text).toContain("started");
		expect(result.text).toContain("Command timed out after 1 seconds");
		expect(Date.now() - startedAt).toBeLessThan(10_000);
	});

	it("renders the solution's edit like the original edit tool", async () => {
		const { harness } = await setup();
		const definition = harness.session.getToolDefinition("edit");
		const args = { path: "math.js", edits: [{ oldText: "values.length - 1", newText: "values.length" }] };
		const fixed = await call(harness, "edit", args);
		const render = (renderers: Parameters<typeof withBuiltInRenderers>[1]) => {
			const component = new ToolExecutionComponent(
				"edit",
				"edit-render",
				args,
				{},
				withBuiltInRenderers("edit", renderers),
				{ requestRender() {} } as unknown as TUI,
				harness.tempDir,
			);
			component.updateResult({
				content: [{ type: "text", text: fixed.text }],
				details: fixed.details,
				isError: false,
			});
			return component.render(100);
		};
		expect(render(definition)).toEqual(render({ ...editRenderers, renderShell: "self" }));
	});
});
