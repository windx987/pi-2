// black travel adapter: price in cents, with 7% VAT.

export const net = 76304;

export function gross() {
	return Math.round(net * 1.07);
}
