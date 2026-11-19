// red office chair: price in cents, with 7% VAT.

export const net = 71602;

export function gross() {
	return Math.round(net * 1.07);
}
