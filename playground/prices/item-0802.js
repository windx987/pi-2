// navy notebook: price in cents, with 7% VAT.

export const net = 68845;

export function gross() {
	return Math.round(net * 1.07);
}
