// blue desk mat: price in cents, with 7% VAT.

export const net = 35261;

export function gross() {
	return Math.round((net * 107) / 100);
}
