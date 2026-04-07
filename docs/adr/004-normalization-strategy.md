# ADR 004: Static Lookup Tables for Role and Location Normalization

**Date:** 2026-04-07
**Status:** Accepted

## Context

Compensation data arrives with inconsistent role titles (`"swe"`, `"SWE II"`, `"Software Dev"`, `"e4"`) and location strings (`"sf"`, `"nyc"`, `"San Francisco, CA"`). Without normalization, the same role at the same company appears as dozens of distinct rows, breaking percentile calculations.

The normalization step runs inside every `process_submission` Celery task, so it must be fast and deterministic.

## Decision

Use **static Python dictionaries** (`ROLE_NORMALIZATION_MAP`, `METRO_MAP`, `CITY_ALIASES`) in `apps/surveys/normalizers.py` as the normalization source of truth, with a simple `dict.get(cleaned_key, fallback)` lookup.

## Reasoning

**Static dicts over a database table:**
- Zero DB queries per normalization call.
- Deterministic: the same input always produces the same output regardless of DB state.
- Version-controlled: changes to normalization rules are captured in git history with a clear diff.
- Testable in isolation without a running database (`test_normalizers.py` has no `@pytest.mark.django_db` marker).

**Canonical lowercased key:** Input is stripped, lowercased, and whitespace-normalized before lookup. This handles `"SWE"`, `" swe "`, `"SWE  "` identically.

**Graceful fallback:** Unknown titles fall back to `.title()` of the original string rather than raising an error. An unknown role is better than a failed submission.

**Family classification:** Titles are also classified into a `family` (`Engineering`, `Product`, `Data`, `Design`, `Other`) via `ROLE_FAMILY_MAP`. This supports family-level filtering without storing the mapping in the DB.

## Trade-offs

- **Maintenance cost:** New role variants must be added manually to the dict. In production, this would likely be replaced or supplemented by a fuzzy matcher (e.g., rapidfuzz edit distance) or an LLM classifier.
- **No feedback loop:** There's no mechanism to discover which submitted titles failed to match. A future improvement would log unmatched titles to a monitoring channel.
- **Static dicts don't scale infinitely:** At tens of thousands of distinct role variants, a fuzzy matching approach becomes necessary. At the current scope (~60 mappings), the dict is readable and fast.

## Consequences

- `normalize_role_title`, `normalize_location`, and `normalize_company_size` are pure functions — no side effects, no DB access.
- `Role` and `Location` ORM objects are created via `get_or_create` using the normalized values as keys, not the raw input.
- Normalization tests run without `@pytest.mark.django_db` and are fast (~0ms each).
