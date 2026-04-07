# ADR 003: Celery + Redis for Asynchronous Submission Processing

**Date:** 2026-04-07
**Status:** Accepted

## Context

Each ingested submission requires normalization (role title lookup, location parsing, company size classification) and a `CompensationRecord` upsert. These operations are fast individually but can be slow in bulk (10k+ records per survey upload). Blocking the HTTP response on all of this work would make the ingest endpoint unacceptably slow.

Additionally, normalization failures should not cause the ingest request to fail — they should be retried and logged without losing the raw submission.

## Decision

Use **Celery** with **Redis** as both broker and result backend. The ingest endpoint enqueues a `process_submission` task for each new submission and returns immediately with a `{submitted, duplicates}` count.

## Reasoning

**Task-per-submission vs. bulk task:**
- One `process_submission` task per submission allows independent retry on failure without re-processing successful records.
- A single bulk task would fail atomically — one bad record aborts the rest.

**Retry with exponential backoff:**
```python
@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_submission(self, submission_id):
    ...
    raise self.retry(exc=exc)
```
Transient errors (DB connection blip, constraint race) retry up to 3 times with a 60-second delay before the submission is marked `failed`.

**`CELERY_TASK_ALWAYS_EAGER=True` in development:**
Tasks execute synchronously in the same process during tests and local development. This avoids requiring a running Redis/worker to develop or test the ingest logic, while keeping production behavior unchanged.

**Redis over RabbitMQ:**
Redis serves double duty as both broker and result backend, reducing infrastructure complexity. At this data volume, Redis queue throughput is more than sufficient. RabbitMQ would only be preferable at much higher task rates or with complex routing requirements.

## Trade-offs

- **Status tracking is eventual:** the ingest endpoint returns before submissions are processed. Callers polling `GET /api/submissions/?status=pending` will see a delay between submission and processing completion.
- **Redis is a single point of failure** for task queuing. In production, Redis Sentinel or a managed Redis (ElastiCache, Upstash) addresses this.
- **No result persistence:** `process_submission` returns a dict but this is only used for debugging. The source of truth for processing state is `SurveySubmission.status`.

## Consequences

- `SurveySubmission.status` transitions: `pending → processing → processed | failed`.
- The worker container runs `celery -A config.celery worker` — a separate Docker Compose service from the web container.
- `bulk_ingest_survey` is a convenience task for seeding/migrations that batches fingerprint checks before dispatching per-submission tasks.
