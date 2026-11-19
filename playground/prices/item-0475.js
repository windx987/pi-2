// green backpack: price in cents, with 7% VAT.

export const net = 33748;

export function gross() {
	return Math.round((net * 107) / 100);
}
