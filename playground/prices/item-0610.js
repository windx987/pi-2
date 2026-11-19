// oak monitor stand: price in cents, with 7% VAT.

export const net = 18315;

export function gross() {
	return Math.round((net * 107) / 100);
}
