// red notebook: price in cents, with 7% VAT.

export const net = 2898;

export function gross() {
	const vat = net * 0.07;
	return Math.round(net + vat);
}
