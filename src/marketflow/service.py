import hashlib, json, time
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from .db import EventRow, SessionLocal
from .metrics import INGEST_BATCHES, INGEST_EVENTS, INGEST_SECONDS, REPLAY_EVENTS
from .schemas import MarketEvent

class BatchTooLarge(ValueError): pass

def event_to_dict(event: MarketEvent) -> dict:
    data = event.model_dump(mode="json")
    data["price"] = str(event.price)
    data["quantity"] = str(event.quantity)
    return data

def ingest_events(events: list[MarketEvent], max_batch_size: int = 5000) -> dict:
    if len(events) > max_batch_size:
        raise BatchTooLarge(f"batch has {len(events)} events; limit is {max_batch_size}")
    started = time.perf_counter(); batch_id = str(uuid4())
    accepted, duplicates, rejected, ids, errors = 0, 0, 0, [], []
    # A single transaction gives batch-level atomicity for successful inserts; duplicates are skipped.
    with SessionLocal() as session:
        try:
            for event in events:
                existing = session.scalar(select(EventRow.id).where(EventRow.event_id == event.event_id))
                if existing is not None:
                    duplicates += 1; INGEST_EVENTS.labels(outcome="duplicate").inc(); continue
                row = EventRow(event_id=event.event_id, symbol=event.symbol,
                    event_time=event.event_time.replace(tzinfo=None),
                    received_time=event.received_time.replace(tzinfo=None) if event.received_time else None,
                    price=event.price, quantity=event.quantity, venue=event.venue, source=event.source)
                session.add(row)
                try:
                    session.flush()
                    accepted += 1; ids.append(event.event_id); INGEST_EVENTS.labels(outcome="accepted").inc()
                except IntegrityError:
                    session.rollback(); duplicates += 1
                    # Re-open transaction for remaining events after a race on unique event_id.
                    session.begin()
            session.commit()
        except Exception:
            session.rollback(); raise
    INGEST_BATCHES.inc(); INGEST_SECONDS.observe(time.perf_counter() - started)
    return {"batch_id": batch_id, "accepted": accepted, "duplicates": duplicates,
            "rejected": rejected, "event_ids": ids, "errors": errors}

def replay_events(symbol: str | None = None, start: datetime | None = None,
                  end: datetime | None = None, limit: int = 10000) -> dict:
    stmt = select(EventRow).order_by(EventRow.event_time.asc(), EventRow.event_id.asc()).limit(limit)
    if symbol: stmt = stmt.where(EventRow.symbol == symbol.upper())
    if start: stmt = stmt.where(EventRow.event_time >= start.replace(tzinfo=None))
    if end: stmt = stmt.where(EventRow.event_time <= end.replace(tzinfo=None))
    with SessionLocal() as session: rows = list(session.scalars(stmt))
    canonical = []
    for row in rows:
        canonical.append({"event_id": row.event_id, "symbol": row.symbol,
            "event_time": row.event_time.isoformat(), "price": str(Decimal(row.price)),
            "quantity": str(Decimal(row.quantity)), "venue": row.venue, "source": row.source})
    encoded = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode()
    REPLAY_EVENTS.inc(len(rows))
    return {"count": len(rows), "digest_sha256": hashlib.sha256(encoded).hexdigest(),
        "first_event_time": rows[0].event_time if rows else None,
        "last_event_time": rows[-1].event_time if rows else None, "events": canonical}
