import { existsSync, mkdirSync, readFileSync, rmSync, writeFileSync } from "fs";
import { tmpdir } from "os";
import { join } from "path";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { executeBashWithOperations } from "../src/core/bash-executor.ts";
import { createLocalBashOperations } from "../src/core/tools/bash.ts";
import * as shellModule from "../src/utils/shell.ts";

// The local shell backend behind the user shell (`!command`) and `user_bash` handlers. These cases
// were part of the bash tool's tests before the workshop edition removed the tool.
describe("local bash operations", () => {
	let testDir: string;

	beforeEach(() => {
		testDir = join(tmpdir(), `local-bash-ops-test-${Date.now()}`);
		mkdirSync(testDir, { recursive: true });
	});

	afterEach(() => {
		vi.restoreAllMocks();
		rmSync(testDir, { recursive: true, force: true });
	});

	it("should throw error when cwd does not exist", async () => {
		const ops = createLocalBashOperations();
		await expect(
			ops.exec("echo test", "/this/directory/definitely/does/not/exist/12345", { onData: () => {} }),
		).rejects.toThrow(/Working directory does not exist/);
	});

	it("should handle process spawn errors", async () => {
		vi.spyOn(shellModule, "getShellConfig").mockReturnValueOnce({
			shell: "/nonexistent-shell-path-xyz123",
			args: ["-c"],
		});

		const ops = createLocalBashOperations();
		await expect(ops.exec("echo test", testDir, { onData: () => {} })).rejects.toThrow(/ENOENT/);
	});

	it("should pass shellPath through to shell resolution", async () => {
		const getShellConfigSpy = vi.spyOn(shellModule, "getShellConfig");
		const ops = createLocalBashOperations({ shellPath: "/custom/bash" });
		await expect(
			ops.exec("echo test", testDir, {
				onData: () => {},
			}),
		).rejects.toThrow("Custom shell path not found: /custom/bash");
		expect(getShellConfigSpy).toHaveBeenCalledWith("/custom/bash");
	});

	it("should send commands over stdin when shell resolution requires it", async () => {
		vi.spyOn(shellModule, "getShellConfig").mockReturnValue({
			shell: process.execPath,
			args: [
				"-e",
				'let input = ""; process.stdin.setEncoding("utf8"); process.stdin.on("data", (chunk) => { input += chunk; }); process.stdin.on("end", () => { process.stdout.write(input); });',
			],
			commandTransport: "stdin",
		});
		const chunks: Buffer[] = [];
		const ops = createLocalBashOperations({ shellPath: "C:\\Windows\\System32\\bash.exe" });
		const nameExpansion = "$" + "{name}";
		const countExpansion = "$" + "{count}";
		const iExpansion = "$" + "{i}";
		const command = `name='World'; echo "Hello, ${nameExpansion}!"; count=3; for i in $(seq 1 ${countExpansion}); do echo "Iteration ${iExpansion} of ${countExpansion}"; done`;

		const result = await ops.exec(command, testDir, {
			onData: (data) => chunks.push(data),
		});

		expect(result.exitCode).toBe(0);
		expect(Buffer.concat(chunks).toString("utf-8")).toBe(command);
	});

	it("should resolve legacy WSL bash.exe to stdin command transport", () => {
		if (process.platform === "win32") return;
		const originalCwd = process.cwd();
		const platformDescriptor = Object.getOwnPropertyDescriptor(process, "platform");
		const shellPath = "C:\\Windows\\System32\\bash.exe";
		writeFileSync(join(testDir, shellPath), "");
		try {
			process.chdir(testDir);
			Object.defineProperty(process, "platform", {
				configurable: true,
				value: "win32",
			});

			expect(shellModule.getShellConfig(shellPath)).toEqual({
				shell: shellPath,
				args: ["-s"],
				commandTransport: "stdin",
			});
		} finally {
			process.chdir(originalCwd);
			if (platformDescriptor) {
				Object.defineProperty(process, "platform", platformDescriptor);
			}
		}
	});

	it("should expose local bash operations for extension reuse", async () => {
		const ops = createLocalBashOperations();
		const chunks: Buffer[] = [];

		const result = await ops.exec("echo $TEST_LOCAL_BASH_OPS", testDir, {
			onData: (data) => chunks.push(data),
			env: { ...process.env, TEST_LOCAL_BASH_OPS: "from-local-ops" },
		});

		expect(result.exitCode).toBe(0);
		expect(Buffer.concat(chunks).toString("utf-8").trim()).toBe("from-local-ops");
	});

	it("should preserve executeBash sanitization when using local bash operations", async () => {
		const result = await executeBashWithOperations(
			"printf '\\033[31mred\\033[0m\\r\\n'",
			process.cwd(),
			createLocalBashOperations(),
		);

		expect(result.exitCode).toBe(0);
		expect(result.output).toBe("red\n");
	});

	it("executeBash should persist full output when truncation happens by line count only", async () => {
		const result = await executeBashWithOperations("seq 3000", process.cwd(), createLocalBashOperations());
		const fullOutputPath = result.fullOutputPath;

		expect(result.truncated).toBe(true);
		expect(fullOutputPath).toBeDefined();

		for (let i = 0; i < 20 && (!fullOutputPath || !existsSync(fullOutputPath)); i++) {
			await new Promise((resolve) => setTimeout(resolve, 10));
		}

		expect(fullOutputPath).toBeDefined();
		expect(existsSync(fullOutputPath!)).toBe(true);
		const fullOutput = readFileSync(fullOutputPath!, "utf-8");
		expect(fullOutput).toContain("1\n2\n3");
		expect(fullOutput).toContain("2998\n2999\n3000");
	});
});
