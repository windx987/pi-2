// steel backpack: price in cents, with 7% VAT.

export const net = 22104;

export function gross() {
	return Math.round(net * 1.07);
}
