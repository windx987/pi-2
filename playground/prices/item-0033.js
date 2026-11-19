// navy monitor stand: price in cents, with 7% VAT.

export const net = 32683;

export function gross() {
	return Math.round(net * 1.07);
}
