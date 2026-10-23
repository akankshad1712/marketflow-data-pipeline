from datetime import datetime, timezone
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

class MarketEvent(BaseModel):
    """Normalized trade/quote event. Prices use Decimal to avoid binary-float drift."""
    model_config = ConfigDict(extra="forbid")
    event_id: str = Field(min_length=1, max_length=128)
    symbol: str = Field(min_length=1, max_length=32)
    event_time: datetime
    received_time: datetime | None = None
    price: Decimal = Field(gt=Decimal("0"), max_digits=20, decimal_places=8)
    quantity: Decimal = Field(gt=Decimal("0"), max_digits=20, decimal_places=8)
    venue: str = Field(default="SIM", min_length=1, max_length=32)
    source: str = Field(default="synthetic", min_length=1, max_length=64)

    @field_validator("event_time", "received_time")
    @classmethod
    def normalize_timestamp(cls, value):
        if value is None:
            return value
        if value.tzinfo is None:
            raise ValueError("timestamps must include a timezone")
        return value.astimezone(timezone.utc)

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, value: str) -> str:
        import re
        normalized = value.strip().upper()
        if not re.fullmatch(r"[A-Z0-9._-]+", normalized):
            raise ValueError("symbol may contain only letters, digits, period, underscore, and hyphen")
        return normalized

    @model_validator(mode="after")
    def validate_time_order(self):
        if self.received_time and self.event_time > self.received_time:
            raise ValueError("event_time cannot be later than received_time")
        return self

class IngestBatch(BaseModel):
    events: list[MarketEvent] = Field(min_length=1)

class IngestResult(BaseModel):
    batch_id: str
    accepted: int
    duplicates: int
    rejected: int
    event_ids: list[str]
    errors: list[dict]

class ReplayRequest(BaseModel):
    symbol: str | None = None
    start: datetime | None = None
    end: datetime | None = None
    limit: int = Field(default=10000, ge=1, le=100000)

class ReplayResult(BaseModel):
    count: int
    digest_sha256: str
    first_event_time: datetime | None
    last_event_time: datetime | None
    events: list[MarketEvent]
