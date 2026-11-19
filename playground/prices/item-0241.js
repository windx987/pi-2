// steel water bottle: price in cents, with 7% VAT.

export const net = 18376;

export function gross() {
	return Math.round(net * 1.07);
}
