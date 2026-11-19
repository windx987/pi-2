// oak laptop sleeve: price in cents, with 7% VAT.

export const net = 7839;

export function gross() {
	return Math.round(net * 1.07);
}
