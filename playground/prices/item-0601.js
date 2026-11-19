// green pencil set: price in cents, with 7% VAT.

export const net = 62460;

export function gross() {
	return Math.round(net * 1.07);
}
