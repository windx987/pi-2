// steel office chair: price in cents, with 7% VAT.

export const net = 65677;

export function gross() {
	return Math.round((net * 107) / 100);
}
