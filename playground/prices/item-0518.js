// red travel adapter: price in cents, with 7% VAT.

export const net = 29038;

export function gross() {
	return Math.round((net * 107) / 100);
}
