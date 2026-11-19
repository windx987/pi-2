# Prices

1000 files, `item-0001.js` to `item-1000.js`, one per product. Each exports:

- `net`: the price without VAT, in whole cents.
- `gross()`: the price with 7% VAT, in whole cents, rounded to the nearest cent (half a cent rounds up).

For example, `net = 1000` gives `gross() = 1070`, and `net = 1235` gives `1321` (1321.45 rounded).

One of the files is wrong.
