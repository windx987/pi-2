// black water bottle: price in cents, with 7% VAT.

export const net = 12773;

export function gross() {
	return Math.round(net * 1.07);
}
