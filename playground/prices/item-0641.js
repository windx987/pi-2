// black mouse pad: price in cents, with 7% VAT.

export const net = 94285;

export function gross() {
	return Math.round(net * 1.07);
}
