// white desk mat: price in cents, with 7% VAT.

export const net = 34030;

export function gross() {
	return Math.round(net * 1.07);
}
