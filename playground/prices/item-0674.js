// red reading light: price in cents, with 7% VAT.

export const net = 78338;

export function gross() {
	return Math.round(net * 1.07);
}
