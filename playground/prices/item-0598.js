// grey travel adapter: price in cents, with 7% VAT.

export const net = 44862;

export function gross() {
	return Math.round(net * 1.07);
}
