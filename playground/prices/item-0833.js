// green coffee mug: price in cents, with 7% VAT.

export const net = 16924;

export function gross() {
	return Math.round(net * 1.07);
}
