// red backpack: price in cents, with 7% VAT.

export const net = 86310;

export function gross() {
	return Math.round(net * 1.07);
}
