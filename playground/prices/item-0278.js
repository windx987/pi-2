// grey desk lamp: price in cents, with 7% VAT.

export const net = 31148;

export function gross() {
	return Math.round((net * 107) / 100);
}
