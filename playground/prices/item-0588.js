// grey wall clock: price in cents, with 7% VAT.

export const net = 56416;

export function gross() {
	return Math.round(net * 1.07);
}
