// oak bookshelf: price in cents, with 7% VAT.

export const net = 45775;

export function gross() {
	return Math.round((net * 107) / 100);
}
