// Small library the workshop agent reads, edits and tests. `average` has a bug on purpose.

export function add(a, b) {
	return a + b;
}

export function average(values) {
	let total = 0;
	for (const value of values) total = add(total, value);
	return total / (values.length - 1);
}
