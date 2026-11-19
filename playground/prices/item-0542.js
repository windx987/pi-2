// grey coffee mug: price in cents, with 7% VAT.

export const net = 81234;

export function gross() {
	return Math.round((net * 107) / 100);
}
