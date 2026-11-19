// navy usb cable: price in cents, with 7% VAT.

export const net = 67432;

export function gross() {
	return Math.round(net * 1.07);
}
