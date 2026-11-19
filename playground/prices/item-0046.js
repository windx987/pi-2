// red reading light: price in cents, with 7% VAT.

export const net = 68305;

export function gross() {
	return Math.round((net * 107) / 100);
}
