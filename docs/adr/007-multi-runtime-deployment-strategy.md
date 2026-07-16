# ADR 007: Multi-Runtime Deployment Strategy — Hetzner + Serverless Container

**Date:** 2026-07-15
**Status:** Proposed

## Context

The solar-ingest-api runs as a docker-compose service on a single Hetzner VPS
(65.108.243.192) alongside every other portfolio-infra container. That
deployment shape is right-sized for actual traffic — the endpoint sees zero
production load, all containers share ~$4/mo of Hetzner compute, and the
architectural patterns (fingerprint dedup, Celery fan-out, DRF throttling,
CQRS-lite analytics) are all demonstrable end-to-end.

Two portfolio pressures push toward a second deployment target on a
managed / serverless runtime:

1. **JD keyword and concept signal.** A pass over the Beacon corpus
   (3,657 active listings, 57 in-pipeline / starred) shows:

   | Concept | Active | Targeted |
   |---|---|---|
   | "serverless" | 95 | 5 |
   | GCP / Google Cloud | 320 | 10 |
   | AWS Lambda | 21 | 2 |
   | Fargate / ECS | ~2 | 0 |
   | Event-driven / queues / SQS / pub-sub | 148 | — |

   Specific vendors (Cloud Run, Cloud SQL, Cloud Tasks, Upstash, Neon)
   have near-zero mention rate (0-6 across 3,657 JDs). Concept-level
   bullets ("serverless patterns", "event-driven architectures", "GCP")
   hit real targeted roles — Luxoft's *"Cloud experience beyond core
   compute/storage/DB — e.g. eventing, queues, serverless"*, Thrive
   Market's *"serverless patterns"*, West Monroe's *"scalable solutions
   across AWS, Azure, and GCP"*.

2. **Portfolio narrative depth.** Every portfolio project currently
   deploys the same way: Hetzner + docker-compose + Caddy + Cloudflare.
   Adding a second-runtime deploy demonstrates the "same architecture,
   different runtime substrate" muscle — the *runtime portability*
   pattern — which is meaningfully different from just showing knowledge
   of managed services on a whiteboard.

## Decision (proposed)

Ship **AWS Fargate + SQS + RDS Postgres** as the primary second-runtime
target. Keep Hetzner as the live demo endpoint. Document the GCP Cloud
Run equivalent side-by-side in this ADR but treat it as optional Phase B
if runtime-fluency signal turns out to matter more than AWS-keyword
signal.

Rationale for AWS-first:

- **Higher JD hit rate in the targeted set.** 21 Lambda + 2 Fargate + a
  large share of the 148 event-driven / SQS mentions land in AWS. Luxoft
  and Thrive Market are explicit AWS shops.
- **Consulting-signal alignment.** Deloitte, West Monroe, and similar
  consultancies (which are a real segment of the targeted set) run
  multi-cloud but historically default to AWS for greenfield.
- **Existing AWS profile.** `claude-deploy` AWS profile already
  configured; no new account bootstrap required.

## The two runtimes side-by-side

Same architecture — fingerprint dedup, Celery-shaped async fan-out,
DRF throttling, JWT auth boundary, `percentile_cont` analytics — mapped
to two different runtime substrates.

| Component | Hetzner (today) | GCP Cloud Run (Phase B) | AWS Fargate (Phase A) |
|---|---|---|---|
| **HTTP compute** | gunicorn in docker-compose | Cloud Run service (scales to zero) | ECS Fargate service behind ALB |
| **Async workers** | Celery worker container | Second Cloud Run service on `/tasks/process` webhook | ECS Fargate task or Lambda triggered by SQS |
| **Broker / queue** | Redis (Celery broker) | Cloud Tasks (HTTP push to worker webhook) | SQS (poll or trigger-based) |
| **Task library** | Celery + Redis transport | `google-cloud-tasks` client + WSGI handler | Celery + SQS transport (`kombu[sqs]`) — keeps `.delay()` shape |
| **Database** | Shared portfolio-postgres | Cloud SQL Postgres OR Neon (autoscaling) | RDS Postgres + RDS Proxy for connection pooling |
| **Connection pooling** | Not needed (long-lived gunicorn) | PgBouncer in front of Cloud SQL, OR Neon (native) | RDS Proxy (managed pooler) |
| **Cache (DRF throttle)** | Redis (portfolio-redis) | Upstash Redis (HTTP-based, no persistent conn) | ElastiCache Serverless Redis |
| **TLS / DNS** | Caddy on VPS + Cloudflare orange | Cloud Run built-in TLS + Cloud DNS + Cloudflare | ALB with ACM cert + Route 53 + Cloudflare |
| **Real-client IP** | `CloudflareRealIPMiddleware` (CF-Connecting-IP) | Same middleware — CF still fronts | Same middleware — CF still fronts |
| **Secrets** | `.env` file on VPS | Secret Manager | Secrets Manager or SSM Parameter Store |
| **Deploy trigger** | git push → SSH rebuild | Cloud Build on push → Cloud Run revision | GitHub Actions → ECR push → ECS service update |
| **Cost profile idle** | ~$4/mo (shared VPS) | $0 (scales to zero) | ~$15-30/mo (ALB + RDS min + minimum Fargate task) |
| **Cost profile spike** | Same $4 (single VPS ceiling) | Pay-per-request, near-linear scale | Fargate task-hour + SQS request + RDS instance |

## What each port actually requires

### Phase A — AWS Fargate + SQS + RDS

**Application changes:**
- `celery -A config worker` command stays the same in the Fargate task
  definition. Broker URL changes from `redis://` to `sqs://` via
  `kombu[sqs]` transport. `.delay()` call sites unchanged.
- Two settings profiles: current `config/settings/production.py` continues
  to work on Hetzner; new `config/settings/aws.py` overrides `CACHES`
  (ElastiCache endpoint), `DATABASES` (RDS Proxy endpoint), and
  `CELERY_BROKER_URL` (SQS URL).
- IAM role for the Fargate task to read SQS + Secrets Manager.

**Infrastructure changes:**
- Terraform module: VPC, ECS cluster, RDS instance + RDS Proxy, SQS
  queue + DLQ, ElastiCache Serverless, ALB + ACM cert, ECR repo, IAM
  roles, CloudWatch log groups.
- GitHub Actions workflow: build → push to ECR → `aws ecs update-service`
  with new task-def revision.
- Cloudflare orange-cloud DNS pointing at ALB.

**Estimated scope:** 1-2 days of focused work. Terraform is the meat;
Django-side changes are ~50 lines.

### Phase B — GCP Cloud Run + Cloud Tasks + Neon

**Application changes:**
- Bigger Celery refactor: Cloud Tasks doesn't have Celery-transport
  parity. Either write a thin `enqueue_task(handler_url, payload)`
  shim that both `.delay()` sites call, or wrap the worker in a
  Flask/Django URL handler and have Cloud Tasks POST to it directly.
  The `process_submission` handler stays intact — the dispatch changes.
- Same two-settings pattern: `config/settings/gcp.py` overrides `CACHES`
  (Upstash), `DATABASES` (Neon), and the task-queue helper.

**Infrastructure changes:**
- Cloud Build triggers on push, deploys new Cloud Run revision.
- Cloud SQL / Neon provisioning.
- Upstash account + Redis instance.
- Cloud Tasks queue + worker service permissions.
- Load balancer + custom domain + managed cert.

**Estimated scope:** 1-2 days of focused work. Cloud Tasks refactor is
the meat; other pieces mostly wire together.

## Reasoning

**Why not do just one runtime port (drop the other):**

Both AWS and GCP appear in targeted JDs; the value is demonstrating
runtime portability, which requires more than one non-Hetzner runtime to
be an actual demonstration. But two full ports is expensive; deferring
Phase B to Phase A's completion (or omitting it if AWS lands the JD
signal) is right-sized.

**Why Fargate over Lambda for AWS:**

- Django + Lambda is possible via Zappa / Mangum but painful — cold
  starts, package size limits, ORM connection thrash.
- Fargate = containerized runtime, same Dockerfile as Hetzner. Minimal
  application-side change.
- "Serverless container" is a well-recognized pattern name — matches
  Thrive Market's *"serverless patterns"* concept without the Lambda
  operational baggage.

**Why keep Hetzner as the live demo:**

- Cost. Idle Cloud Run / Fargate is either zero (Cloud Run) or ~$15-30/mo
  (Fargate ALB + RDS minimum) — real money vs shared $4 Hetzner VPS.
- Deploy simplicity. Live demo of the audit patterns benefits from being
  reachable in <30s from a git-pull, which the current SSH rebuild
  supports and a Terraform-managed AWS deploy makes clunkier.
- Portfolio narrative. "Same app, three deployment targets" — Hetzner,
  AWS, GCP — is a stronger interview story than "I ported it once".

**Why NOT decouple Celery from the app first:**

The current handler-registry pattern from ADR 005 lets us swap the task
dispatch layer per-runtime without touching the handlers themselves. The
existing `process_submission.delay(id)` call becomes a runtime-specific
enqueue function — one line per deploy target. No refactor prerequisite;
the plugin pattern already isolated the seam.

## Consequences

**Positive:**

- Multi-runtime deploy substantially expands the JD-bullet coverage —
  from "we run Django on a VPS" (near-nothing in the corpus) to
  concrete AWS Lambda / SQS / RDS Fargate story that hits 148+ active
  and 5+ targeted JDs' event-driven / serverless bullets.
- Demonstrates the *runtime portability* pattern in practice, not just
  in-conversation. Same idempotency / async / CQRS / auth architecture,
  three substrates.
- Forces a settings-profile discipline (`production.py` / `aws.py` /
  `gcp.py`) that's an interview-visible artifact in its own right —
  environment abstraction as a bounded interface.

**Negative:**

- Real AWS spend (~$15-30/mo idle for Fargate + ALB + RDS min) unless
  we tear it down between demos. Cost management becomes a real task
  (auto-shutdown Lambda, or accept the burn).
- Terraform state maintenance — one more piece of infra to babysit.
  Existing Hetzner setup is mostly stateless (git-pull + rebuild); AWS
  adds ECR image lifecycle, Secrets Manager rotation, RDS backup, etc.
- Two-settings-file discipline requires care — every setting added to
  `production.py` has to be considered for whether it belongs in the
  shared base or in a runtime-specific file. Cross-runtime drift is a
  real failure mode.

**Neutral:**

- The extraction from ADR 005 (`apps.surveys` as a kernel with plugin
  handlers) is orthogonal to this ADR. Both ports work identically on
  the current single-consumer setup and the future multi-consumer setup.
- Neither runtime port makes the audit patterns from the 2026-07-15
  security fixes obsolete — SECRET_KEY fail-fast, throttle-identity
  chain, CF-Connecting-IP middleware — all still apply verbatim.

## Follow-ups

- If Phase A ships, update `architecture-mapping.md` §13 to add
  "runtime portability" and "serverless container" to Core Patterns.
- If neither ships this quarter, revisit whether the JD-signal
  argument still holds — corpus refreshes weekly; the counts may
  shift as new roles land.
- Consider a small "deployment README" per-runtime under
  `docs/deploy/{hetzner,aws,gcp}.md` so anyone reading the repo can
  see the substrate-per-substrate contract.
