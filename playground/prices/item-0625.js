// red plant pot: price in cents, with 7% VAT.

export const net = 48546;

export function gross() {
	return Math.round(net * 1.07);
}
