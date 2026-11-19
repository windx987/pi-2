// steel headphones: price in cents, with 7% VAT.

export const net = 55433;

export function gross() {
	return Math.round((net * 107) / 100);
}
