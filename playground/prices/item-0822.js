// red reading light: price in cents, with 7% VAT.

export const net = 85777;

export function gross() {
	return Math.round(net * 1.07);
}
