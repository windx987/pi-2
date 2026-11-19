// white office chair: price in cents, with 7% VAT.

export const net = 95774;

const VAT = 0.07;

export function gross() {
	return Math.round(net + net * VAT);
}
