// blue monitor stand: price in cents, with 7% VAT.

export const net = 44342;

export function gross() {
	return Math.round(net * 1.07);
}
