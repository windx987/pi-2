# INC-04: login outage

- Date: 2026-05-07, 23:40 UTC
- Service: auth
- Severity: SEV1

## Summary

No one could log in for 14 minutes.

## Root cause

The token signing key expired and the rotation job had been disabled a week earlier.

## Fix

Re-enable the rotation job and alert when a key is close to expiry.
