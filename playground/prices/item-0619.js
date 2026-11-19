// steel monitor stand: price in cents, with 7% VAT.

export const net = 66984;

export function gross() {
	return Math.round(net * 1.07);
}
