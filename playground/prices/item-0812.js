// grey plant pot: price in cents, with 7% VAT.

export const net = 19319;

export function gross() {
	return Math.round(net * 1.07);
}
