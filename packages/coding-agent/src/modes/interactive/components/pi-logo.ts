import { backgroundAnsi, foregroundAnsi, isAppleTerminalSession, rgbColor } from "@earendil-works/pi-tui";
import { theme } from "../theme/theme.ts";

const CORAL = rgbColor(228, 138, 122);
const BLUE = rgbColor(79, 142, 179);
const YELLOW = rgbColor(234, 182, 93);
const MINT = rgbColor(121, 191, 163);
const RESET = "\x1b[0m";

/**
 * The pi/2 logo: the pi mark (4 cells), a slash (4 cells) and a 2 (3 cells), 2 lines tall. Each cell shows
 * two square pixels with half blocks:
 *
 *   coral coral coral .        .    .    .    mint     coral coral coral
 *   blue  .     coral .        .    .    mint .        .     .     coral
 *   blue  blue  .     yellow   .    mint .    .        coral .     .
 *   blue  .     .     yellow   mint .    .    .        coral coral coral
 *
 * The brand colors stay fixed across themes; they follow the terminal's color mode.
 */
export function piLogoLines(): [string, string] {
	const mode = theme.getColorMode();
	const fg = (color: typeof CORAL) => foregroundAnsi(color, mode);
	// The fourth cell of the pi mark's top line is empty, so it is padded to the same width as the bottom line.
	const top = `${fg(CORAL)}${backgroundAnsi(BLUE, mode)}▀${RESET}${fg(CORAL)}▀█${RESET}    ${fg(MINT)}▄▀${RESET} ${fg(CORAL)}▀▀█${RESET}`;
	const bottom = `${fg(BLUE)}█▀${RESET} ${fg(YELLOW)}█${RESET} ${fg(MINT)}▄▀${RESET}   ${fg(CORAL)}█▄▄${RESET}`;
	return [top, bottom];
}

/**
 * Whether the terminal renders the half-block logo correctly. Apple Terminal draws gaps between rows and
 * misaligns the half blocks, so it gets the text wordmark instead.
 */
export function supportsPiLogo(): boolean {
	return !isAppleTerminalSession();
}

/** Text fallback for the logo: "Pi/2" with the logo's colors. */
export function piWordmark(): string {
	const mode = theme.getColorMode();
	const fg = (color: typeof CORAL) => foregroundAnsi(color, mode);
	return `${fg(CORAL)}P${RESET}${fg(YELLOW)}i${RESET}${fg(MINT)}/${RESET}${fg(CORAL)}2${RESET}`;
}
