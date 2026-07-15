# ADR 005: Extract `apps.surveys` into a Domain-Agnostic Ingest Kernel

**Date:** 2026-07-15
**Status:** Accepted (Phase 1 shipped) / Proposed (Phase 2)

## Context

`apps.surveys` currently hosts a reusable ingest pipeline — fingerprint-based
idempotency, Celery fan-out, an explicit state machine on `QuoteSubmission`,
retry policy, JSON-body validation, DRF viewset. The domain-specific logic
(brand→tier lookup, location→metro map, cost-per-watt derivation, `SolarQuote`
upsert) lives in `apps.compensation`, but the two are tightly coupled: the
Celery task `process_quote` imports the compensation models and normalizers
directly.

Two directions of pressure to loosen that coupling:

1. **Portfolio narrative.** The ingest primitives are reusable across
   domains (job listings, real-estate listings, medical claims, product
   catalogs — anything with dedup + async normalize + analytics shape).
   Encapsulating them as a plugin host demonstrates the "spot a reusable
   primitive inside a working system" muscle interviewers probe for.

2. **Legacy naming debt.** `apps.surveys` and `apps.compensation` are names
   from the pre-2026-07 salary-survey domain (`Survey`, `Role`,
   `CompensationRecord`). Models were repurposed on 2026-04 (commit `a06b178`)
   and 2026-07 (commit `3f29fc7`) but app labels, table prefixes, and
   directory names still carry the old vocabulary. Reading the code today
   requires holding two mental models: what the file/table is *called*
   versus what it *does*.

## Decision

Extract in two phases via **strangler-fig discipline** — keep the live URL
surface (`solar-ingest.danhle.net/api/*`) working continuously, no big-bang
cutover.

### Phase 1 (shipped 2026-07-15)

Minimum-invasive introduction of the plugin extension point. No renames,
no endpoint changes, no data migration beyond one additive field.

- `apps/surveys/handlers.py` — module-level registry with
  `@register_ingest_handler(key, validator=…)` decorator, `get_handler(key)`
  lookup, `get_record_validator(key)` lookup, `UnknownIngestHandler`
  exception. The optional `validator` is a DRF Serializer class that the
  generic `IngestRequestSerializer` runs per-record; handlers that accept
  any-shape input can omit it.
- `QuoteSource.handler_key: CharField` — default `"solar_quote"` so every
  existing source auto-opts into the current behavior.
- `apps/surveys/tasks.process_quote` renamed to `process_submission`;
  body becomes a thin dispatcher (`handler = get_handler(...)`).
  Handler owns normalization and domain-row persistence.
- `apps/compensation/handlers.solar_quote_handler` — receives the solar
  normalization body verbatim, registers under `"solar_quote"` with
  `SolarQuoteRecordSerializer` (moved from `apps/surveys/serializers.py`
  to `apps/compensation/serializers.py`) as its record validator.
- `apps/surveys/serializers.IngestRequestSerializer` — becomes generic:
  validates envelope (`quote_source_id` exists, `records` is a bounded
  list) then dispatches per-record validation to whichever DRF Serializer
  the source's handler registered.
- `apps/compensation/apps.SolarConfig.ready()` — imports handlers module
  to trigger registration at Django boot.
- `apps/jobposts/` — new second-consumer skeleton. Stub `"job_post"`
  handler with a minimal `JobPostRecordSerializer` (title required, plus
  optional company/location/salary); no persistence yet. Proves the
  extension point works end-to-end (API validation → handler dispatch).

**Backward compat:** all existing rows in `QuoteSource` get
`handler_key="solar_quote"` from the migration's `default=`, so the live
endpoint's behavior is unchanged. Existing tests (which exercise the solar
path) continue to pass.

**What Phase 1 does NOT do (intentionally deferred):**

- No rename of `apps.surveys` → `apps.ingest_core`.
- No rename of `apps.compensation` → `apps.solar_quotes`.
- No rename of `QuoteSubmission` → `Submission`, `QuoteSource` → `IngestSource`.
- No change to URL routes (`/api/quote-sources/`, `/api/submissions/`
  stay).
- No table renames (`surveys_quotesource`, `compensation_solarquote` stay).
- No real domain model for `apps.jobposts` (no `JobListing` model, no
  analytics endpoint, no salary parser).

### Phase 2 (proposed — separate session)

Complete the extraction and pay down the legacy naming debt.

**Package + model renames (biggest diff):**

- `apps.surveys` → `apps.ingest_core`. All imports across the tree updated.
  Django settings `INSTALLED_APPS` updated. Migration files under the old
  path get moved.
- `apps.compensation` → `apps.solar_quotes`. Same treatment.
- `QuoteSubmission` → `Submission` (kernel model, domain-agnostic name).
- `QuoteSource` → `IngestSource`.

**Data migration:** the risky part. Options in order of preference:

1. **`Meta.db_table` overrides** on the renamed models pointing at the
   existing table names (`surveys_quotesource`, `surveys_quotesubmission`,
   `compensation_solarquote`, etc). Zero data migration, tables stay put.
   Downside: table names permanently mismatch model names — same legacy
   debt, just moved from code to schema. Accept it and document why.
2. **`RenameModel` migrations** with matching `db_table` renames. Clean
   final state. Requires downtime or a two-phase deploy (old + new names
   coexisting behind a compatibility layer). Overkill for a portfolio demo.

Recommendation: **Option 1** (db_table overrides). One-time comment in each
model explaining that the table name is legacy from the salary-survey
origin story. Zero migration risk.

**URL rewrites:**

- `/api/quote-sources/` → `/api/ingest-sources/` (with a redirect for the
  old path so external callers don't break).
- `/api/submissions/` stays (already generic).
- `/api/ingest/` stays (already generic).
- The solar-specific `/api/quotes/summary/` and `/api/quotes/` stay under
  `/api/solar-quotes/`  — this is domain analytics, belongs in
  `apps.solar_quotes`'s URL namespace.

**Real `apps.jobposts` domain:**

- `JobListing` model — title, company, salary_min/max, currency, location,
  posted_at, source_url.
- Normalizers — company → canonical name, salary → USD/annual band,
  location → metro (reusable via extraction from `apps.solar_quotes.normalizers`
  if location logic really is generic; otherwise keep separate).
- Analytics endpoint — `/api/job-postings/summary/?title_family=engineer&location=CA`
  returning salary p25/p50/p75/p90 by band, same shape as the solar cost
  summary.
- Handler upgrade from Phase 1's log-only stub to the full persistence
  pipeline.
- Own admin, own serializers, own DRF viewset.

**Interview narrative once Phase 2 lands:**

> *"solar-ingest-api started as a salary-survey pipeline in 2026-04, got
> repurposed to solar quotes in 2026-07, and then I extracted the reusable
> ingest kernel — fingerprint dedup, Celery fan-out, state machine — into
> a shared app that now hosts two domains: solar quotes and job listings.
> Adding a third domain is a new Django app plus one
> `@register_ingest_handler` decorator. That's the plugin-pattern
> discipline applied inside a monolith — bounded contexts + shared kernel,
> no premature service extraction."*

## Reasoning

**Why plugin registry vs. abstract base class + subclass inheritance:**

The registry pattern is more decoupled — consumers don't need to know
about the kernel's internals, just the handler callable signature. ABC
inheritance would couple every consumer to the kernel's class hierarchy
and make testing consumers-in-isolation harder.

**Why strangler-fig (in-place additive) vs. clean rewrite:**

`solar-ingest.danhle.net` is live and demonstrating an audit lesson about
production-grade defensive coding. A rewrite would take the endpoint
offline. Additive change with a default `handler_key` value means zero
observable behavior change on Phase 1 landing.

**Why defer the rename to Phase 2:**

Renames are cheap-per-file but expensive-per-attention. Doing them in the
same commit as the plugin extraction would make it hard to review either
change cleanly. Two focused commits > one large commit with intermixed
motivations.

## Consequences

**Positive:**
- Kernel and consumer(s) are now decoupled. Adding a third domain is a
  new app with a `handlers.py` — no changes to the kernel required.
- The ingest pipeline's behavior is now explicit in one file
  (`apps.surveys.tasks.process_submission`) — reading it, you see the
  state machine and the dispatch point, not a mix of state machine and
  domain logic.
- The Phase 2 renames can be evaluated on their own merits without being
  entangled with the architectural change.

**Negative:**
- Two-part cognitive model until Phase 2: files still called `surveys`
  and `compensation` when they mean `ingest_core` and `solar_quotes`.
  Every code reader has to hold "the name doesn't match the current
  intent" for a while.
- Every new domain has to remember to register its handler in `apps.py`
  `ready()`. Forgetting is a silent bug (submissions FAIL with
  `UnknownIngestHandler`). Mitigation: a management command like
  `manage.py check_ingest_handlers` that verifies every distinct
  `QuoteSource.handler_key` value has a registered handler.

**Neutral:**
- The `apps.jobposts` skeleton in Phase 1 is a promise, not a feature.
  Anyone reading the code sees the second-consumer shape but there's
  nothing to actually POST there yet. Documented above so it doesn't look
  like abandoned work.
