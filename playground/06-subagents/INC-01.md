# INC-01: catalog degraded

- Date: 2026-03-11, 10:35 UTC
- Service: catalog
- Severity: SEV2

## Summary

Product pages loaded slowly for about 20 minutes.

## Root cause

The cache was flushed during a deploy, so every request went to the database.

## Fix

Warm the cache before sending traffic to a new instance.
