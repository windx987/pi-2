// grey phone case: price in cents, with 7% VAT.

export const net = 58453;

const VAT = 0.07;

export function gross() {
	return Math.round(net + net * VAT);
}
