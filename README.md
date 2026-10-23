# MarketFlow — Reliable Market Data Pipeline & Replay Engine

A portfolio-grade backend for a quant research/data engineering workflow. It demonstrates schema contracts, idempotent ingestion, timestamp/price validation, deterministic event replay, observability, containerized deployment, and automated tests using synthetic data. It is an educational project, **not** a trading system and does not connect to a broker or exchange.

## Architecture

```text
Synthetic/source events -> Pydantic contract -> authenticated FastAPI -> idempotent DB writer
                                                            |               |
                                                            v               v
                                                       Prometheus       PostgreSQL
                                                            ^               |
                                                            |               v
                                                   /metrics <--- deterministic replay + SHA-256 digest
```

## Features

- **Strict event contract:** required identifiers, normalized symbols, timezone-aware timestamps, positive decimal price/quantity, no unexpected fields, and event/receive-time ordering.
- **Idempotent ingestion:** stable `event_id` and database uniqueness constraint prevent duplicate persistence.
- **Deterministic replay:** stable sort order (`event_time`, `event_id`) and canonical JSON serialization produce a SHA-256 digest for repeatability checks.
- **Operational visibility:** Prometheus counters and latency histogram for accepted/duplicate events, batch count, ingestion duration, and replay count.
- **API security baseline:** `X-API-Key` for ingestion and replay endpoints. Replace this simple shared-key approach with an identity provider/rotation strategy in a real deployment.
- **Production-shaped workflow:** Docker Compose, Postgres health checks, environment-based configuration, CI workflow, pytest suite, synthetic event generator.

## Quick start (local)

Requires Python 3.11+.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install -e '.[dev]'
cp .env.example .env  # Windows PowerShell: Copy-Item .env.example .env
uvicorn marketflow.api:app --reload
```

Open http://127.0.0.1:8000/docs. The default SQLite database is for local development only.

## Docker Compose (PostgreSQL)

```bash
docker compose up --build
```

API: http://localhost:8000 · Docs: http://localhost:8000/docs · Metrics: http://localhost:8000/metrics

## Generate and ingest sample events

```bash
python scripts/generate_sample.py --count 100 --out sample_events.json
```

Send generated JSON to the API using Python, curl, or the interactive docs. Example curl for a single event:

```bash
curl -X POST http://localhost:8000/v1/events \
  -H 'Content-Type: application/json' -H 'X-API-Key: local-dev-key-change-me' \
  -d '{"events":[{"event_id":"demo-1","symbol":"NIFTY","event_time":"2025-01-02T09:15:00+00:00","received_time":"2025-01-02T09:15:00.010+00:00","price":"23000.50","quantity":"10","venue":"SIM","source":"manual"}]}'
```

Replay events (with API key):

```bash
curl -X POST http://localhost:8000/v1/replay \
  -H 'Content-Type: application/json' -H 'X-API-Key: local-dev-key-change-me' \
  -d '{"symbol":"NIFTY","limit":1000}'
```

Run tests: `pytest`. Lint: `ruff check src tests`.

## Data contract / validation rules

1. `event_id` is mandatory and unique in persistence.
2. `symbol` must match uppercase alphanumeric/period/underscore/hyphen symbols.
3. `event_time` and optional `received_time` must be timezone-aware and are normalized to UTC at the API boundary.
4. `event_time` cannot be later than `received_time` when both exist.
5. Price and quantity must be strictly positive decimal values.
6. Extra fields are rejected so schema drift is explicit.
7. Batch size is bounded by `MAX_BATCH_SIZE`.
8. Replay order is deterministic and constrained by optional symbol/time filters and a maximum limit.

## Reliability notes and next steps

This starter uses a synchronous SQLAlchemy transaction path and a shared API key. For a more demanding production deployment, add: a proper migration tool (Alembic), retry/backoff with bounded jitter, a dead-letter table/queue for malformed raw payloads, Kafka/Redpanda consumer offsets and replay semantics, partitioning/retention policies, OpenTelemetry traces, Prometheus alert rules, load tests, and secrets management. If enabling Kafka, document at-least-once delivery and idempotent sink behavior explicitly.

**Honest portfolio metrics:** the repository contains tests and instrumentation, but does not claim a measured throughput, 99.9% success rate, or recovery time. Run repeatable load/failure tests and report actual results with hardware, batch size, and test duration before adding numbers to a resume.

## Suggested resume bullet (only after verifying implementation)

“Built a Python market-data ingestion and replay service with strict Pydantic contracts, duplicate-safe persistence, deterministic SHA-256 replay checks, FastAPI authentication, Prometheus metrics, PostgreSQL/Docker deployment, and automated validation tests.”

## License
MIT — see `LICENSE`.
