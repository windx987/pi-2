// white notebook: price in cents, with 7% VAT.

export const net = 46590;

export function gross() {
	return Math.round((net * 107) / 100);
}
