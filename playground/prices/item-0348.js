// grey usb cable: price in cents, with 7% VAT.

export const net = 84047;

export function gross() {
	return Math.round((net * 107) / 100);
}
