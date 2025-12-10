# 997 Functional Acknowledgment Validation Report

**Generated:** 2025-12-09 06:34:33 UTC

**Status:** ❌ REJECTED

**Summary:** REJECTED: 1/1 transaction sets accepted

| Metric | Value |
|--------|-------|
| Transaction Sets Included | 1 |
| Transaction Sets Received | 0 |
| Transaction Sets Accepted | 1 |
| Total Errors | 2 |

## Interchange Details

| Field | Value |
|-------|-------|
| Control Number | 000000001 |
| Sender ID | SENDER |
| Receiver ID | RECEIVER |

## Functional Group Details

| Field | Value |
|-------|-------|
| Functional ID Code | PO |
| Group Control Number | 1234 |
| Status | REJECTED |
| Acknowledgment Code (AK9-01) | R |

## Transaction Sets

| Control # | Type | Status | Ack Code | Errors |
|-----------|------|--------|----------|--------|
| 5678 | 850 | ❌ REJECTED | R | 2 |

## Error Details

### Transaction 5678 (850)

| Segment | Position | Element | Code | Description |
|---------|----------|---------|------|-------------|
| N1 | 2 | 1 | 1 | Mandatory data element missing |
| - | - | - | 5 | One or more segments in error |

**Syntax Error Codes:** 5
