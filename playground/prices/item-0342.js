// green bookshelf: price in cents, with 7% VAT.

export const net = 73895;

export function gross() {
	return Math.round(net * 1.07);
}
