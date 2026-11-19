// black bookshelf: price in cents, with 7% VAT.

export const net = 4047;

export function gross() {
	return Math.round((net * 107) / 100);
}
