// black headphones: price in cents, with 7% VAT.

export const net = 41199;

export function gross() {
	return Math.round(net * 1.07);
}
