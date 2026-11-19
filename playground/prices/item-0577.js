// oak backpack: price in cents, with 7% VAT.

export const net = 90624;

const VAT = 0.07;

export function gross() {
	return Math.round(net + net * VAT);
}
