// grey bookshelf: price in cents, with 7% VAT.

export const net = 11847;

export function gross() {
	return Math.round((net * 107) / 100);
}
