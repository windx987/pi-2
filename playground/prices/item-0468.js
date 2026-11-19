// blue desk mat: price in cents, with 7% VAT.

export const net = 52981;

export function gross() {
	return Math.round(net * 1.07);
}
