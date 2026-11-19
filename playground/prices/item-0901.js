// black bookshelf: price in cents, with 7% VAT.

export const net = 40803;

export function gross() {
	return Math.round(net * 1.07);
}
