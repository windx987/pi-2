// navy pencil set: price in cents, with 7% VAT.

export const net = 19785;

export function gross() {
	return Math.round((net * 107) / 100);
}
