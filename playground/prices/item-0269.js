// red wall clock: price in cents, with 7% VAT.

export const net = 76281;

export function gross() {
	return Math.round((net * 107) / 100);
}
