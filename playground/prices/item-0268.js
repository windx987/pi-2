// black laptop sleeve: price in cents, with 7% VAT.

export const net = 25809;

const VAT = 0.07;

export function gross() {
	return Math.round(net + net * VAT);
}
