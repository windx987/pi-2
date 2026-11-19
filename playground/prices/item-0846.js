// steel mouse pad: price in cents, with 7% VAT.

export const net = 97432;

export function gross() {
	return Math.round(net * 1.07);
}
