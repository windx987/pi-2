// blue office chair: price in cents, with 7% VAT.

export const net = 75088;

export function gross() {
	const vat = net * 0.07;
	return Math.round(net + vat);
}
