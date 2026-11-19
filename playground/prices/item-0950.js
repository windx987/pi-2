// navy backpack: price in cents, with 7% VAT.

export const net = 30433;

export function gross() {
	return Math.round(net * 1.07);
}
