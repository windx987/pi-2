// yellow pencil set: price in cents, with 7% VAT.

export const net = 91847;

export function gross() {
	return Math.round((net * 107) / 100);
}
