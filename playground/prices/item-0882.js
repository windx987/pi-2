// white wall clock: price in cents, with 7% VAT.

export const net = 88448;

export function gross() {
	return Math.round((net * 107) / 100);
}
