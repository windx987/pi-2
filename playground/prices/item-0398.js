// black desk lamp: price in cents, with 7% VAT.

export const net = 77971;

export function gross() {
	return Math.round(net * 1.07);
}
