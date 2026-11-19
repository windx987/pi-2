// black phone case: price in cents, with 7% VAT.

export const net = 49987;

export function gross() {
	return Math.round(net * 1.07);
}
