// navy bookshelf: price in cents, with 7% VAT.

export const net = 86446;

export function gross() {
	return Math.round((net * 107) / 100);
}
