// blue laptop sleeve: price in cents, with 7% VAT.

export const net = 39724;

export function gross() {
	return Math.round((net * 107) / 100);
}
