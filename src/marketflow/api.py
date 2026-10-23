import hmac
from fastapi import Depends, FastAPI, Header, HTTPException, Request, Response
from fastapi.responses import PlainTextResponse
from .config import settings
from .db import init_db
from .metrics import metrics_payload
from .schemas import IngestBatch, ReplayRequest
from .service import BatchTooLarge, ingest_events, replay_events

app = FastAPI(title="MarketFlow", version="1.0.0", description="Validated, idempotent market-data ingestion and deterministic replay")

@app.on_event("startup")
def startup(): init_db()

async def require_api_key(x_api_key: str | None = Header(default=None)):
    if not x_api_key or not hmac.compare_digest(x_api_key, settings.api_key):
        raise HTTPException(status_code=401, detail="Invalid or missing API key")

@app.get("/health")
def health(): return {"status": "ok", "service": "marketflow"}

@app.post("/v1/events", dependencies=[Depends(require_api_key)])
def ingest(batch: IngestBatch):
    try: return ingest_events(batch.events, settings.max_batch_size)
    except BatchTooLarge as exc: raise HTTPException(status_code=413, detail=str(exc)) from exc

@app.post("/v1/replay", dependencies=[Depends(require_api_key)])
def replay(request: ReplayRequest):
    if request.start and request.end and request.start > request.end:
        raise HTTPException(status_code=422, detail="start must be <= end")
    return replay_events(request.symbol, request.start, request.end, request.limit)

@app.get("/metrics", response_class=PlainTextResponse)
def metrics():
    payload, content_type = metrics_payload()
    return Response(content=payload, media_type=content_type)
