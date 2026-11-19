// red water bottle: price in cents, with 7% VAT.

export const net = 2604;

export function gross() {
	return Math.round((net * 107) / 100);
}
