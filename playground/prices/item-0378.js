// green mouse pad: price in cents, with 7% VAT.

export const net = 93809;

export function gross() {
	return Math.round((net * 107) / 100);
}
