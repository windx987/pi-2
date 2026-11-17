import { win32 } from "node:path";
import { getPowerShellConfig } from "../../utils/shell.ts";
import { type BashOperations, type BashToolDetails, type BashToolInput, createLocalShellOperations } from "./bash.ts";

const UTF8_OUTPUT_PREFIX = "try { [Console]::OutputEncoding=[System.Text.Encoding]::UTF8 } catch {}\n";

// Windows PowerShell 5.1 turns redirected native stderr into error records and sets $? to false, so
// `git push 2>&1 | Select-Object -Last 3` exits 1 although git exited 0 (#8842). PowerShell 7 does not.
// Exit 0 when the last failure is only such a record and the native command exited 0; otherwise keep the
// -Command rule: 0 when the last statement succeeded, 1 when it failed. The lone `;` keeps an unfinished last
// statement, such as `Get-ChildItem |`, a parse error instead of continuing into the suffix and running.
const WINDOWS_POWERSHELL_EXIT_SUFFIX =
	'\n;\nif ($?) { exit 0 }\nif (($LASTEXITCODE -eq 0) -and ("$($Error[0].FullyQualifiedErrorId)" -like "NativeCommandError*")) { exit 0 }\nexit 1';

export type PowerShellOperations = BashOperations;
export type PowerShellToolDetails = BashToolDetails;
export type PowerShellToolInput = BashToolInput;

export function createLocalPowerShellOperations(): PowerShellOperations {
	return {
		exec: async (command, cwd, options) => {
			const shellConfig = getPowerShellConfig();
			// A final backtick would continue the user's last line into the suffix, so leave such commands unchanged.
			const suffix =
				win32.basename(shellConfig.shell).toLowerCase() === "powershell.exe" && !command.endsWith("`")
					? WINDOWS_POWERSHELL_EXIT_SUFFIX
					: "";
			return createLocalShellOperations("PowerShell", () => shellConfig).exec(
				`${UTF8_OUTPUT_PREFIX}${command}${suffix}`,
				cwd,
				options,
			);
		},
	};
}
