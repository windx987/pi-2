// navy coffee mug: price in cents, with 7% VAT.

export const net = 92560;

export function gross() {
	return Math.round(net * 1.07);
}
