// steel coffee mug: price in cents, with 7% VAT.

export const net = 76559;

export function gross() {
	return Math.round(net * 1.07);
}
