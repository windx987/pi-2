// steel desk lamp: price in cents, with 7% VAT.

export const net = 26683;

export function gross() {
	return Math.round(net * 1.07);
}
