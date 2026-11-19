// yellow plant pot: price in cents, with 7% VAT.

export const net = 90095;

export function gross() {
	return Math.round((net * 107) / 100);
}
