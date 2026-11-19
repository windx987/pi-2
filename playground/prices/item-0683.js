// blue headphones: price in cents, with 7% VAT.

export const net = 16632;

export function gross() {
	return Math.round((net * 107) / 100);
}
