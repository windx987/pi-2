// green phone case: price in cents, with 7% VAT.

export const net = 86982;

export function gross() {
	return Math.trunc(net * 1.07);
}
