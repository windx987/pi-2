// red travel adapter: price in cents, with 7% VAT.

export const net = 2038;

export function gross() {
	return Math.round(net * 1.07);
}
