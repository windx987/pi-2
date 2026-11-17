import assert from "node:assert/strict";
import { test } from "node:test";
import { add, average } from "./math.js";

test("add adds two numbers", () => {
	assert.equal(add(2, 3), 5);
});

test("average of 2, 4 and 6 is 4", () => {
	assert.equal(average([2, 4, 6]), 4);
});
