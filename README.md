# Solar Ingest API

A Django REST API that ingests, deduplicates, and normalizes solar installation quote data into a structured PostgreSQL schema. Built to demonstrate Django + DRF + Celery proficiency applied to the residential solar market.

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
                                               │  QuoteSubmission │
                                               │  SolarQuote      │
                                               │  SystemConfig    │
                                               │  Location        │
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

export DATABASE_URL=postgres://solar_user:changeme@localhost:5432/solar_db
export REDIS_URL=redis://localhost:6379/0
export SECRET_KEY=dev-key
export DJANGO_SETTINGS_MODULE=config.settings.development

python manage.py migrate
python manage.py runserver
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/quote-sources/` | List all quote sources |
| `POST` | `/api/quote-sources/` | Create a quote source |
| `GET` | `/api/quote-sources/<id>/` | Get quote source detail |
| `PUT/PATCH` | `/api/quote-sources/<id>/` | Update quote source |
| `DELETE` | `/api/quote-sources/<id>/` | Delete quote source |
| `POST` | `/api/ingest/` | Ingest solar quote records |
| `GET` | `/api/submissions/` | List submissions (filterable by status, source) |
| `GET` | `/api/quotes/` | List solar quotes (filterable) |
| `GET` | `/api/quotes/summary/` | Percentile summary (p25/p50/p75/p90) by state or system size |
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

### Create a quote source
```bash
curl -X POST http://localhost:8000/api/quote-sources/ \
  -H "Content-Type: application/json" \
  -d '{"name": "SunRun CA 2024", "installer_name": "sunrun", "quote_year": 2024}'
```

### Ingest solar quotes
```bash
curl -X POST http://localhost:8000/api/ingest/ \
  -H "Content-Type: application/json" \
  -d '{
    "quote_source_id": 1,
    "records": [
      {
        "panel_brand": "LG NeON 2",
        "location": "San Diego, CA",
        "system_size_kw": 7.2,
        "system_cost": 25200,
        "installer_type": "local"
      },
      {
        "panel_brand": "SunPower Maxeon 3",
        "location": "Phoenix, AZ",
        "system_size_kw": 9.6,
        "cost_per_watt": 3.45,
        "installer_type": "national"
      }
    ]
  }'
```

### Query cost-per-watt summary
```bash
curl "http://localhost:8000/api/quotes/summary/?state=CA&system_size_band=5-8+kW"
```

Response:
```json
{
  "state": "CA",
  "system_size_band": "5-8 kW",
  "p25": 2.95,
  "p50": 3.35,
  "p75": 3.75,
  "p90": 4.20,
  "sample_size": 120
}
```

### Filter solar quotes
```bash
# Filter by panel tier and state
curl "http://localhost:8000/api/quotes/?panel_tier=premium&state=CA"

# Filter by system size band and installer type
curl "http://localhost:8000/api/quotes/?system_size_band=5-8+kW&installer_type=local"
```

## Running Tests

```bash
pip install -r requirements/development.txt
pytest
pytest --cov=apps --cov-report=term-missing
pytest tests/surveys/test_views.py -v
```

## Normalization Logic

The ingest pipeline normalizes:
- **Panel brands**: Mapped to tiers — `premium-plus` (SunPower), `premium` (LG/Panasonic/REC/QCells), `standard` (LONGi/Jinko/Canadian Solar/Trina)
- **System size**: kW or watts → size band (`3-5 kW`, `5-8 kW`, `8-12 kW`, `12 kW+`)
- **Locations**: City/state parsing, metro area grouping, alias resolution (`sf` → San Francisco, `la` → Los Angeles)
- **Installer type**: Free-text → enum (`local`, `regional`, `national`, `utility`)
- **Cost derivation**: `cost_per_watt` derived from `system_cost / watts` if not provided directly

Deduplication uses SHA-256 fingerprint of the canonical JSON representation of each record.
