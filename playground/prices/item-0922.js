// navy desk lamp: price in cents, with 7% VAT.

export const net = 6038;

export function gross() {
	const vat = net * 0.07;
	return Math.round(net + vat);
}
