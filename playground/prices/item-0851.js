// grey water bottle: price in cents, with 7% VAT.

export const net = 56329;

export function gross() {
	return Math.round(net * 1.07);
}
