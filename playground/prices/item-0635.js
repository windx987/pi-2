// grey travel adapter: price in cents, with 7% VAT.

export const net = 92212;

export function gross() {
	return Math.round((net * 107) / 100);
}
