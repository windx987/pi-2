// red mouse pad: price in cents, with 7% VAT.

export const net = 70859;

export function gross() {
	return Math.round((net * 107) / 100);
}
