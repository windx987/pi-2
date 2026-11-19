// green keyboard: price in cents, with 7% VAT.

export const net = 10582;

export function gross() {
	const vat = net * 0.07;
	return Math.round(net + vat);
}
