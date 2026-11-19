// steel coffee mug: price in cents, with 7% VAT.

export const net = 77260;

export function gross() {
	return Math.round((net * 107) / 100);
}
