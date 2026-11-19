// green headphones: price in cents, with 7% VAT.

export const net = 21168;

export function gross() {
	return Math.round(net * 1.07);
}
