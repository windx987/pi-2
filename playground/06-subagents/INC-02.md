# INC-02: checkout failures

- Date: 2026-04-02, 18:10 UTC
- Service: checkout
- Severity: SEV1

## Summary

Some customers were charged twice when a payment timed out.

## Root cause

The retry loop reused the same idempotency key after the first attempt expired.

## Fix

Keep the key for the whole retry window and check the payment status before retrying.
