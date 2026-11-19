// green pencil set: price in cents, with 7% VAT.

export const net = 10653;

const VAT = 0.07;

export function gross() {
	return Math.round(net + net * VAT);
}
