from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

INGEST_EVENTS = Counter("marketflow_ingest_events_total", "Events handled by ingestion", ["outcome"])
INGEST_BATCHES = Counter("marketflow_ingest_batches_total", "Ingestion batches handled")
INGEST_SECONDS = Histogram("marketflow_ingest_batch_seconds", "Batch ingestion duration")
REPLAY_EVENTS = Counter("marketflow_replay_events_total", "Events emitted by replay")

def metrics_payload():
    return generate_latest(), CONTENT_TYPE_LATEST
