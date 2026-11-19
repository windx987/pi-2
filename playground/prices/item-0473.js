// black pencil set: price in cents, with 7% VAT.

export const net = 40166;

export function gross() {
	return Math.round((net * 107) / 100);
}
