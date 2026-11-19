// yellow plant pot: price in cents, with 7% VAT.

export const net = 955;

export function gross() {
	return Math.round((net * 107) / 100);
}
