# Compensation Ingest API

A Django REST API service that ingests, deduplicates, and normalizes compensation survey data into a structured PostgreSQL schema. Built to demonstrate Django + DRF + Celery proficiency in the compensation intelligence domain.

## Architecture

```
┌─────────────────┐     POST /api/ingest/     ┌──────────────────┐
│   API Client    │ ─────────────────────────> │  IngestView      │
└─────────────────┘                            │  (DRF CBV)       │
                                               └────────┬─────────┘
                                                        │ SHA-256 dedup
                                                        │ queue task
                                                        ▼
                                               ┌──────────────────┐
                                               │  Celery Worker   │
                                               │  (Redis broker)  │
                                               └────────┬─────────┘
                                                        │ normalize
                                                        ▼
                                               ┌──────────────────┐
                                               │   PostgreSQL     │
                                               │  SurveySubmission│
                                               │  CompensRecord   │
                                               │  Role / Location │
                                               └──────────────────┘
```

## Setup

### Docker Compose (recommended)

```bash
cp .env.example .env
# Edit .env and set DATABASE_PASSWORD and SECRET_KEY

docker-compose up -d --build
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
```

The API will be available at `http://localhost:8000`.

### Local Development

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements/development.txt

export DATABASE_URL=postgres://compensation_user:changeme@localhost:5432/compensation_db
export REDIS_URL=redis://localhost:6379/0
export SECRET_KEY=dev-key
export DJANGO_SETTINGS_MODULE=config.settings.development

python manage.py migrate
python manage.py runserver
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/surveys/` | List all surveys |
| `POST` | `/api/surveys/` | Create a survey |
| `GET` | `/api/surveys/<id>/` | Get survey detail |
| `PUT/PATCH` | `/api/surveys/<id>/` | Update survey |
| `DELETE` | `/api/surveys/<id>/` | Delete survey |
| `POST` | `/api/ingest/` | Ingest compensation records |
| `GET` | `/api/submissions/` | List submissions (filterable by status, survey) |
| `GET` | `/api/compensation/` | List compensation records (filterable) |
| `GET` | `/api/compensation/summary/` | Percentile summary (p25/p50/p75/p90) |
| `POST` | `/api/token/` | Obtain JWT token |
| `POST` | `/api/token/refresh/` | Refresh JWT token |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | sqlite | PostgreSQL connection URL |
| `REDIS_URL` | `redis://localhost:6379/0` | Celery broker / result backend |
| `SECRET_KEY` | insecure default | Django secret key |
| `DJANGO_SETTINGS_MODULE` | development | Settings module to use |
| `DEBUG` | `False` | Enable debug mode |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | Comma-separated allowed hosts |

## Sample API Calls

### Create a survey
```bash
curl -X POST http://localhost:8000/api/surveys/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Levels.fyi 2024", "source": "levels", "year": 2024}'
```

### Ingest compensation records
```bash
curl -X POST http://localhost:8000/api/ingest/ \
  -H "Content-Type: application/json" \
  -d '{
    "survey_id": 1,
    "records": [
      {
        "role_title": "Senior Software Engineer",
        "location": "San Francisco, CA",
        "base_salary": 200000,
        "total_comp": 320000,
        "level": "L5",
        "years_experience": 7,
        "company_size": "enterprise"
      },
      {
        "role_title": "swe",
        "location": "Austin, TX",
        "total_comp": 145000,
        "company_size": "mid"
      }
    ]
  }'
```

### Query compensation summary
```bash
curl "http://localhost:8000/api/compensation/summary/?role=Senior+Software+Engineer&level=L5"
```

Response:
```json
{
  "role": "Senior Software Engineer",
  "level": "L5",
  "p25": 240000.0,
  "p50": 300000.0,
  "p75": 380000.0,
  "p90": 450000.0,
  "sample_size": 42
}
```

### Filter compensation records
```bash
# Filter by company size and level
curl "http://localhost:8000/api/compensation/?company_size=enterprise&level=L5"

# Filter by role (partial match)
curl "http://localhost:8000/api/compensation/?role=Software+Engineer"
```

## Running Tests

```bash
# Install dev dependencies
pip install -r requirements/development.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=apps --cov-report=term-missing

# Run a specific test file
pytest tests/surveys/test_views.py -v
```

## Normalization Logic

The ingest pipeline normalizes:
- **Role titles**: 60+ abbreviation mappings (`swe` → `Software Engineer`, `l5` → `Senior Software Engineer`, etc.)
- **Locations**: City/state parsing, metro area grouping, alias resolution (`sf` → San Francisco Bay Area)
- **Company sizes**: Free-text → enum (`faang` → `enterprise`, `Series A` → `startup`, numeric headcounts)

Deduplication uses SHA-256 fingerprint of the canonical JSON representation of each record.
