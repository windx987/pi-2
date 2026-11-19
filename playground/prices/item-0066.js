// black pencil set: price in cents, with 7% VAT.

export const net = 24512;

export function gross() {
	return Math.round(net * 1.07);
}
