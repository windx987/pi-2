// white pencil set: price in cents, with 7% VAT.

export const net = 62377;

export function gross() {
	const vat = net * 0.07;
	return Math.round(net + vat);
}
