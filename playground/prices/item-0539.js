// white reading light: price in cents, with 7% VAT.

export const net = 93013;

const VAT = 0.07;

export function gross() {
	return Math.round(net + net * VAT);
}
