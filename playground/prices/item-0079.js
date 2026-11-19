// green wall clock: price in cents, with 7% VAT.

export const net = 41995;

export function gross() {
	return Math.round(net * 1.07);
}
