// grey headphones: price in cents, with 7% VAT.

export const net = 95504;

export function gross() {
	return Math.round(net * 1.07);
}
