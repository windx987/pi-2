// navy headphones: price in cents, with 7% VAT.

export const net = 96916;

export function gross() {
	return Math.round(net * 1.07);
}
