// oak office chair: price in cents, with 7% VAT.

export const net = 29400;

export function gross() {
	return Math.round((net * 107) / 100);
}
