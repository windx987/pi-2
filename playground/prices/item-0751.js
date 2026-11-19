// red monitor stand: price in cents, with 7% VAT.

export const net = 17698;

export function gross() {
	return Math.round(net * 1.07);
}
