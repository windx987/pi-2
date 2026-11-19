// grey phone case: price in cents, with 7% VAT.

export const net = 32319;

export function gross() {
	return Math.round((net * 107) / 100);
}
