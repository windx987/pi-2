// red usb cable: price in cents, with 7% VAT.

export const net = 12356;

export function gross() {
	return Math.round(net * 1.07);
}
