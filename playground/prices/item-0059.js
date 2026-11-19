// oak mouse pad: price in cents, with 7% VAT.

export const net = 53676;

export function gross() {
	return Math.round((net * 107) / 100);
}
