// white coffee mug: price in cents, with 7% VAT.

export const net = 23339;

export function gross() {
	return Math.round(net * 1.07);
}
