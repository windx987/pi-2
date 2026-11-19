// white pencil set: price in cents, with 7% VAT.

export const net = 90569;

export function gross() {
	return Math.round((net * 107) / 100);
}
