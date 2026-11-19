// white keyboard: price in cents, with 7% VAT.

export const net = 33615;

export function gross() {
	return Math.round(net * 1.07);
}
