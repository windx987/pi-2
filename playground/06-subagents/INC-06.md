# INC-06: duplicate invoices

- Date: 2026-06-03, 09:15 UTC
- Service: billing
- Severity: SEV3

## Summary

A small group of customers received the same invoice email twice.

## Root cause

The monthly job retried after a timeout even though the first run had finished.

## Fix

Record the run before sending and skip an invoice that was already sent.
