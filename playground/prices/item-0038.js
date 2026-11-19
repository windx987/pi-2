// navy desk mat: price in cents, with 7% VAT.

export const net = 38299;

export function gross() {
	return Math.round(net * 1.07);
}
