// green wall clock: price in cents, with 7% VAT.

export const net = 48589;

export function gross() {
	return Math.round(net * 1.07);
}
