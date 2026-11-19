// grey desk lamp: price in cents, with 7% VAT.

export const net = 11284;

export function gross() {
	return Math.round(net * 1.07);
}
