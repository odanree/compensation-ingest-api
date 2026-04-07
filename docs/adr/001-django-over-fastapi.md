# ADR 001: Use Django + DRF Over FastAPI

**Date:** 2026-04-07
**Status:** Accepted

## Context

This service ingests compensation survey data from external sources, normalizes it, and stores it in PostgreSQL. The primary engineering decision was which Python web framework to use. The team has existing FastAPI/SQLAlchemy experience from the broader pipeline project.

Compa's backend stack is Django-based. The goal of this project is to demonstrate fluency with Django's patterns — ORM, migrations, admin, CBVs — not just general Python web development.

## Decision

Use **Django 5** with **Django REST Framework** rather than FastAPI.

## Reasoning

**Django ORM over SQLAlchemy:**
- `get_or_create` and `update_or_create` are first-class ORM patterns, which map cleanly to the deduplication and upsert logic in the ingest pipeline.
- Django migrations handle schema evolution with a single `makemigrations` / `migrate` workflow, avoiding Alembic configuration.
- `select_related` and `prefetch_related` solve N+1 queries at the ORM layer without raw SQL or loader patterns.

**DRF over manual routing:**
- `generics.ListCreateAPIView` and `generics.RetrieveUpdateDestroyAPIView` eliminate boilerplate for standard CRUD while remaining fully overridable (`get_queryset`, `create`).
- `FilterSet` (django-filter) integrates with DRF's `filter_backends` cleanly, keeping filter logic separate from view logic.
- `PageNumberPagination` is configured globally in `REST_FRAMEWORK` settings, giving consistent behavior across all endpoints.

**Django Admin:**
- Zero-cost admin interface for `Survey`, `SurveySubmission`, and `CompensationRecord`. Useful for internal data inspection without a separate frontend.

## Trade-offs

- **FastAPI** would give faster startup, native async, and automatic OpenAPI docs. For this domain (survey ingestion, not a high-throughput API), these aren't meaningful advantages.
- Django's synchronous ORM means Celery handles all async work. This is the right separation: the web layer is thin, heavy processing is offloaded.
- DRF's CBV pattern is more verbose than FastAPI's function decorators, but aligns with Compa's existing codebase conventions.

## Consequences

- All views are class-based (no `@api_view` decorators).
- Celery handles async processing; `CELERY_TASK_ALWAYS_EAGER=True` in development keeps tests synchronous without mocking.
- The admin is registered for all models by default — useful for debugging ingestion issues.
