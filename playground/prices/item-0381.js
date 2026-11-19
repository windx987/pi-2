// red coffee mug: price in cents, with 7% VAT.

export const net = 94805;

export function gross() {
	return Math.round((net * 107) / 100);
}
