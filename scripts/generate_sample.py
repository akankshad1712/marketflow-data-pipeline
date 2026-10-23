import argparse, json, random
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="Generate deterministic synthetic market events")
    parser.add_argument("--count", type=int, default=100); parser.add_argument("--out", default="sample_events.json")
    parser.add_argument("--seed", type=int, default=7); args = parser.parse_args()
    if args.count < 1: parser.error("--count must be >= 1")
    rng = random.Random(args.seed); start = datetime(2025, 1, 2, 9, 15, tzinfo=timezone.utc); price = Decimal("250.00")
    rows=[]
    for i in range(args.count):
        price += Decimal(str(round(rng.uniform(-0.4, 0.4), 2)))
        t = start + timedelta(milliseconds=i * 100)
        rows.append({"event_id": f"SIM-{i:08d}", "symbol": rng.choice(["NIFTY", "BANKNIFTY", "RELIANCE"]),
          "event_time": t.isoformat(), "received_time": (t+timedelta(milliseconds=3)).isoformat(),
          "price": str(max(price, Decimal("1"))), "quantity": str(rng.randint(1, 250)), "venue": "SIM", "source": "synthetic"})
    Path(args.out).write_text(json.dumps({"events": rows}, indent=2)); print(f"Wrote {len(rows)} synthetic events to {args.out}")
if __name__ == "__main__": main()
