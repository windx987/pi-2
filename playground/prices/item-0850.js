// red water bottle: price in cents, with 7% VAT.

export const net = 27555;

export function gross() {
	return Math.round(net * 1.07);
}
