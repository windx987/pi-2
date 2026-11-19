// oak monitor stand: price in cents, with 7% VAT.

export const net = 63616;

export function gross() {
	return Math.round(net * 1.07);
}
