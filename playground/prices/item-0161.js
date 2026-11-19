// red notebook: price in cents, with 7% VAT.

export const net = 73867;

export function gross() {
	return Math.round((net * 107) / 100);
}
