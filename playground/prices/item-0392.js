// steel backpack: price in cents, with 7% VAT.

export const net = 35115;

export function gross() {
	const vat = net * 0.07;
	return Math.round(net + vat);
}
