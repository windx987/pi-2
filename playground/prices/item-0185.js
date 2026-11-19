// oak pencil set: price in cents, with 7% VAT.

export const net = 92610;

export function gross() {
	return Math.round((net * 107) / 100);
}
