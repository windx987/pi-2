# INC-03: slow search

- Date: 2026-04-19, 08:05 UTC
- Service: search
- Severity: SEV3

## Summary

Search results took more than five seconds for two hours.

## Root cause

A nightly index rebuild ran while the old index was still serving queries.

## Fix

Build the new index beside the old one and switch over when it is ready.
