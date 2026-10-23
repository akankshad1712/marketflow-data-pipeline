from datetime import datetime, timezone
import pytest
from pydantic import ValidationError
from marketflow.schemas import MarketEvent

def valid_event(**overrides):
    data = {"event_id":"e-1", "symbol":"nifty", "event_time":"2025-01-01T10:00:00+00:00",
      "received_time":"2025-01-01T10:00:01+00:00", "price":"100.25", "quantity":"2", "venue":"SIM", "source":"test"}
    data.update(overrides); return data

def test_symbol_normalized(): assert MarketEvent(**valid_event()).symbol == "NIFTY"
@pytest.mark.parametrize("field,value", [("price", "0"), ("quantity", "-1"), ("symbol", "lower case !")])
def test_rejects_invalid_values(field, value):
    with pytest.raises(ValidationError): MarketEvent(**valid_event(**{field:value}))
def test_rejects_naive_timestamp():
    with pytest.raises(ValidationError): MarketEvent(**valid_event(event_time="2025-01-01T10:00:00"))
def test_rejects_event_after_received():
    with pytest.raises(ValidationError): MarketEvent(**valid_event(event_time="2025-01-01T10:00:02+00:00"))
