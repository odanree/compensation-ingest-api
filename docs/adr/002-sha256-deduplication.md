# ADR 002: SHA-256 Fingerprint for Submission Deduplication

**Date:** 2026-04-07
**Status:** Accepted

## Context

Compensation survey data arrives from multiple sources (Levels.fyi, internal HR exports, third-party vendors) and may be re-submitted across ingestion runs. Without deduplication, the same data point would be processed multiple times, inflating percentile calculations and polluting the dataset.

The ingest endpoint must be **idempotent**: submitting the same record twice should have no effect on the stored data.

## Decision

Compute a **SHA-256 hash of the canonicalized JSON representation** of each raw submission record and store it as a unique `fingerprint` field on `SurveySubmission`.

```python
@classmethod
def compute_fingerprint(cls, raw_data: dict) -> str:
    canonical = json.dumps(raw_data, sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(canonical.encode()).hexdigest()
```

Use `get_or_create(fingerprint=fingerprint, defaults={...})` to make the ingest path atomic.

## Reasoning

**Canonical JSON (`sort_keys=True`):** Key ordering in Python dicts is insertion-order, which varies by source. Sorting keys ensures `{"a": 1, "b": 2}` and `{"b": 2, "a": 1}` produce the same fingerprint.

**SHA-256 over MD5/SHA-1:** Collision resistance is important — a collision would silently suppress a legitimate new record. SHA-256 provides 256-bit collision resistance with negligible performance cost at this data volume.

**Hash of raw payload, not normalized fields:** Deduplication happens before normalization. This means two records with different raw role titles that normalize to the same title are still treated as separate submissions (different sources, different data points). This is intentional: normalization is lossy, and source data should be preserved.

**`db_index=True` on `fingerprint`:** The `get_or_create` lookup hits this index on every ingest call.

## Trade-offs

- **Content-addressed deduplication** means a record with one field changed (e.g., a corrected salary) will be treated as a new submission rather than an update. This is acceptable — corrections should be submitted as new records, with the old one marked superseded if needed.
- **No fuzzy deduplication** (e.g., detecting near-duplicate records with similar salaries). That is a data quality concern outside the scope of the ingestion service.

## Consequences

- `SurveySubmission.fingerprint` has a `UNIQUE` constraint enforced at the database level.
- The ingest endpoint returns `{"submitted": N, "duplicates": M}` — callers can observe how many records were new vs. already seen.
- Tests must generate unique payloads per factory instance (use `LazyAttributeSequence` to vary at least one field).
