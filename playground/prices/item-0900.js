// navy keyboard: price in cents, with 7% VAT.

export const net = 37554;

export function gross() {
	return Math.round(net * 1.07);
}
