// white keyboard: price in cents, with 7% VAT.

export const net = 23666;

export function gross() {
	return Math.round((net * 107) / 100);
}
