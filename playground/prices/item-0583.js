// navy travel adapter: price in cents, with 7% VAT.

export const net = 70272;

export function gross() {
	return Math.round(net * 1.07);
}
