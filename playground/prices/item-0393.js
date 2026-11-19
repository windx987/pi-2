// black keyboard: price in cents, with 7% VAT.

export const net = 51425;

export function gross() {
	return Math.round(net * 1.07);
}
