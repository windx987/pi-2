# INC-05: delayed notifications

- Date: 2026-05-21, 14:25 UTC
- Service: notifications
- Severity: SEV2

## Summary

Email notifications arrived up to 90 minutes late.

## Root cause

One worker was stuck on a large batch and the queue had no second consumer.

## Fix

Add a second consumer and split batches by size.
