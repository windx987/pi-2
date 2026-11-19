// navy mouse pad: price in cents, with 7% VAT.

export const net = 74831;

export function gross() {
	const vat = net * 0.07;
	return Math.round(net + vat);
}
