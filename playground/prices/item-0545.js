// navy keyboard: price in cents, with 7% VAT.

export const net = 85623;

export function gross() {
	return Math.round(net * 1.07);
}
