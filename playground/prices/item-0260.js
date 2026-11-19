// red water bottle: price in cents, with 7% VAT.

export const net = 80468;

export function gross() {
	return Math.round(net * 1.07);
}
