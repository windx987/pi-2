// navy laptop sleeve: price in cents, with 7% VAT.

export const net = 78140;

export function gross() {
	return Math.round(net * 1.07);
}
