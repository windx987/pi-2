import { execFileSync } from "node:child_process";
import { cpSync, mkdtempSync, rmSync, symlinkSync, writeFileSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";
import { fauxAssistantMessage, fauxToolCall, type JsonObject } from "@earendil-works/pi-ai";
import { afterAll, afterEach, beforeAll, describe, expect, it } from "vitest";
import { DefaultResourceLoader } from "../../src/core/resource-loader.ts";
import { SettingsManager } from "../../src/core/settings-manager.ts";
import { createHarness, type Harness } from "./harness.ts";

const educationDir = join(import.meta.dirname, "../../../../education");
const solutions = ["01-read", "02-write", "03-edit", "04-bash"].map((name) =>
	join(educationDir, "exercises", name, "solution.ts"),
);
const IMAGE = "node:22-bookworm-slim";

/** Containers started from the workshop image that still exist, running or not. */
function workshopContainers(): string[] {
	return execFileSync("docker", ["ps", "--all", "--quiet", "--filter", `ancestor=${IMAGE}`], { encoding: "utf-8" })
		.split("\n")
		.filter(Boolean);
}

async function waitForNoContainers(): Promise<string[]> {
	// `--rm` removes a container shortly after it stops.
	for (let i = 0; i < 50 && workshopContainers().length > 0; i++) await new Promise((r) => setTimeout(r, 100));
	return workshopContainers();
}

// Runs the bash solution against a real Docker daemon and checks the isolation the exercise promises.
// Opt-in with PI_WORKSHOP_DOCKER=1, and the image pulled. The workspace must be a directory the Docker
// VM shares: under the home directory for Colima, so this test points TMPDIR there.
describe.skipIf(process.env.PI_WORKSHOP_DOCKER !== "1")("workshop bash solution in real Docker", () => {
	const harnesses: Harness[] = [];
	const originalTmpdir = process.env.TMPDIR;
	let sharedTmp = "";

	beforeAll(() => {
		// The harness works in a directory under os.tmpdir(); put that under the home directory.
		sharedTmp = mkdtempSync(join(homedir(), ".pi-workshop-docker-test-"));
		process.env.TMPDIR = sharedTmp;
	});

	afterAll(() => {
		process.env.TMPDIR = originalTmpdir;
		rmSync(sharedTmp, { recursive: true, force: true });
	});

	afterEach(() => {
		while (harnesses.length > 0) harnesses.pop()?.cleanup();
	});

	async function setup(): Promise<{ harness: Harness; workspace: string }> {
		const resourceLoader = new DefaultResourceLoader({
			cwd: sharedTmp,
			agentDir: join(sharedTmp, "agent"),
			settingsManager: SettingsManager.inMemory(),
			additionalExtensionPaths: solutions,
		});
		await resourceLoader.reload();
		expect(resourceLoader.getExtensions().errors).toEqual([]);
		const harness = await createHarness({ resourceLoader });
		harnesses.push(harness);
		cpSync(join(educationDir, "playground"), harness.tempDir, { recursive: true });
		return { harness, workspace: harness.tempDir };
	}

	/** One model turn that calls bash with `args`, through the normal tool lifecycle. */
	async function bash(harness: Harness, args: JsonObject) {
		harness.setResponses([
			fauxAssistantMessage([fauxToolCall("bash", args)], { stopReason: "toolUse" }),
			fauxAssistantMessage("done"),
		]);
		await harness.session.prompt("run");
		const result = harness.session.messages.filter((message) => message.role === "toolResult").at(-1);
		if (result?.role !== "toolResult") throw new Error("no bash result");
		const text = result.content.map((block) => (block.type === "text" ? block.text : "")).join("");
		return { text, isError: result.isError };
	}

	it("runs commands in the mounted workspace", async () => {
		const { harness, workspace } = await setup();
		const failing = await bash(harness, { command: "node --test" });
		expect(failing).toMatchObject({ isError: true });
		expect(failing.text).toContain("Command exited with code 1");
		const created = await bash(harness, { command: "pwd; echo made > made.txt; ls" });
		expect(created.text).toContain("/workspace");
		expect(created.text).toContain("math.test.js");
		expect(execFileSync("cat", [join(workspace, "made.txt")], { encoding: "utf-8" })).toBe("made\n");
	}, 60_000);

	it("has no network", async () => {
		const { harness } = await setup();
		const dns = await bash(harness, { command: "getent hosts example.com" });
		expect(dns).toMatchObject({ isError: true });
		const fetched = await bash(harness, {
			command: `node -e "fetch('https://example.com').then(() => process.exit(0), () => process.exit(3))"`,
		});
		expect(fetched).toMatchObject({ isError: true });
		expect(fetched.text).toContain("Command exited with code 3");
	}, 60_000);

	it("sees no host files outside the workspace, also through symlinks", async () => {
		const { harness, workspace } = await setup();
		writeFileSync(join(homedir(), ".pi-workshop-docker-secret"), "host secret\n");
		try {
			symlinkSync(homedir(), join(workspace, "host-home"));
			const result = await bash(harness, {
				command:
					"ls /Users /home 2>&1; cat host-home/.pi-workshop-docker-secret 2>&1; ln -s / root-link && ls root-link/",
			});
			expect(result.text).not.toContain("host secret");
			expect(result.text).toContain("No such file or directory");
			// The container's own root, which has the mount point; the host root has none.
			expect(result.text).toMatch(/\bworkspace\b/);
		} finally {
			rmSync(join(homedir(), ".pi-workshop-docker-secret"), { force: true });
		}
	}, 60_000);

	it("enforces the memory and process limits", async () => {
		const { harness } = await setup();
		const limits = await bash(harness, {
			command: "cat /sys/fs/cgroup/memory.max /sys/fs/cgroup/pids.max",
		});
		expect(limits.text.split("\n").slice(0, 2)).toEqual(["1073741824", "256"]);
		const memory = await bash(harness, {
			command: `node -e "const a = []; for (;;) a.push(Buffer.alloc(1e8, 1))"`,
		});
		expect(memory).toMatchObject({ isError: true });
		expect(memory.text).toContain("Command exited with code 137");
		const processes = await bash(harness, {
			command: `node -e "const { spawn } = require('child_process'); let spawned = 0, refused = 0; for (let i = 0; i < 400; i++) { const c = spawn('sleep', ['30']); c.on('spawn', () => spawned++); c.on('error', () => refused++); } setTimeout(() => { console.log('spawned', spawned, 'refused', refused); process.exit(0); }, 1000)"`,
		});
		const [, spawned, refused] = /spawned (\d+) refused (\d+)/.exec(processes.text) ?? [];
		expect(Number(spawned)).toBeLessThan(256);
		expect(Number(refused)).toBeGreaterThan(0);
	}, 120_000);

	it("stops the container at the timeout and leaves no container behind after errors", async () => {
		const { harness } = await setup();
		const startedAt = Date.now();
		const timedOut = await bash(harness, { command: "echo started; sleep 300", timeout: 2 });
		expect(timedOut).toMatchObject({ isError: true });
		expect(timedOut.text).toContain("Command timed out after 2 seconds");
		expect(Date.now() - startedAt).toBeLessThan(20_000);
		expect(await waitForNoContainers()).toEqual([]);

		const failed = await bash(harness, { command: "exit 7" });
		expect(failed.text).toContain("Command exited with code 7");
		expect(await waitForNoContainers()).toEqual([]);
	}, 60_000);
});
