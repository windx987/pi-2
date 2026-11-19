// red reading light: price in cents, with 7% VAT.

export const net = 78105;

export function gross() {
	return Math.round(net * 1.07);
}
