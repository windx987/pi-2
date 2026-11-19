// white monitor stand: price in cents, with 7% VAT.

export const net = 842;

export function gross() {
	return Math.round(net * 1.07);
}
