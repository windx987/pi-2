// navy water bottle: price in cents, with 7% VAT.

export const net = 52241;

export function gross() {
	return Math.round((net * 107) / 100);
}
