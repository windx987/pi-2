// grey reading light: price in cents, with 7% VAT.

export const net = 41825;

export function gross() {
	return Math.round((net * 107) / 100);
}
