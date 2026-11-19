// oak plant pot: price in cents, with 7% VAT.

export const net = 52770;

export function gross() {
	return Math.round(net * 1.07);
}
