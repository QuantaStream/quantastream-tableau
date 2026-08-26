#!/usr/bin/env python3
"""Load Tableau Sample Superstore Orders CSV into qstream-loader.

The script accepts either Tableau's original Sample Superstore headers or the
normalized snake_case headers documented in samples/superstore/README.md. It
posts normalized event envelopes to the QuantaStream JSON loader endpoint.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable

HEADER_MAP = {
    "Row ID": "row_id",
    "Order ID": "order_id",
    "Order Date": "order_date",
    "Ship Date": "ship_date",
    "Ship Mode": "ship_mode",
    "Customer ID": "customer_id",
    "Customer Name": "customer_name",
    "Segment": "segment",
    "Country": "country_region",
    "Country/Region": "country_region",
    "City": "city",
    "State": "state_province",
    "State/Province": "state_province",
    "Postal Code": "postal_code",
    "Region": "region",
    "Product ID": "product_id",
    "Category": "category",
    "Sub-Category": "sub_category",
    "Sub Category": "sub_category",
    "Product Name": "product_name",
    "Sales": "sales",
    "Quantity": "quantity",
    "Discount": "discount",
    "Profit": "profit",
}

REQUIRED_HEADERS = [
    "row_id",
    "order_id",
    "order_date",
    "ship_date",
    "ship_mode",
    "customer_id",
    "customer_name",
    "segment",
    "country_region",
    "city",
    "state_province",
    "postal_code",
    "region",
    "product_id",
    "category",
    "sub_category",
    "product_name",
    "sales",
    "quantity",
    "discount",
    "profit",
]

INT_FIELDS = {"row_id", "quantity"}
FLOAT_FIELDS = {"sales", "discount", "profit"}
DATE_FIELDS = {"order_date", "ship_date"}

DATE_FORMATS = (
    "%Y-%m-%d",
    "%m/%d/%Y",
    "%m/%d/%y",
    "%d-%m-%Y",
    "%d/%m/%Y",
)


@dataclass
class LoadStats:
    rows: int = 0
    emitted: int = 0
    accepted: int = 0
    failed: int = 0


def normalize_header(header: str) -> str:
    text = header.strip()
    return HEADER_MAP.get(text, text.lower().replace(" ", "_"))


def parse_date(value: str) -> str:
    text = value.strip()
    if not text:
        return ""
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            pass
    return text


def coerce_value(field: str, value: str):
    text = value.strip()
    if text == "":
        return None
    if field in INT_FIELDS:
        return int(float(text))
    if field in FLOAT_FIELDS:
        return float(text.replace(",", ""))
    if field in DATE_FIELDS:
        return parse_date(text)
    return text


def normalize_row(row: dict[str, str]) -> dict[str, object]:
    normalized = {normalize_header(k): v for k, v in row.items()}
    missing = [name for name in REQUIRED_HEADERS if name not in normalized]
    if missing:
        raise ValueError("missing required normalized headers: " + ", ".join(missing))
    return {name: coerce_value(name, normalized.get(name, "")) for name in REQUIRED_HEADERS}


def event_for_row(data: dict[str, object], event_type: str, source: str) -> dict[str, object]:
    row_id = data.get("row_id")
    order_id = data.get("order_id") or row_id
    order_date = data.get("order_date")
    event_time = f"{order_date}T00:00:00Z" if order_date else None
    event = {
        "mode": "batch",
        "event_id": f"superstore.order.{row_id}",
        "source": source,
        "source_offset": f"superstore:{row_id}",
        "shard_key": f"superstore.order.{order_id}",
        "payload": {
            "type": event_type,
            "data": data,
        },
    }
    if event_time:
        event["event_time"] = event_time
    return event


def iter_events(path: Path, event_type: str, source: str, limit: int = 0) -> Iterable[dict[str, object]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError("input CSV has no header row")
        for idx, row in enumerate(reader, start=1):
            if limit and idx > limit:
                break
            yield event_for_row(normalize_row(row), event_type, source)


def post_batch(target: str, events: list[dict[str, object]], timeout: float) -> tuple[int, int]:
    body = json.dumps({"events": events}, separators=(",", ":")).encode("utf-8")
    request = urllib.request.Request(target, data=body, method="POST")
    request.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = response.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"loader POST failed: {exc.code} {exc.reason}: {detail}") from exc
    if not payload.strip():
        return len(events), 0
    decoded = json.loads(payload)
    return int(decoded.get("accepted", 0)), int(decoded.get("failed", 0))


def load_csv(path: Path, args: argparse.Namespace) -> LoadStats:
    stats = LoadStats()
    pending = set()

    def submit_batch(executor: ThreadPoolExecutor, batch: list[dict[str, object]]) -> None:
        if not batch:
            return
        pending.add(executor.submit(post_batch, args.target, batch, args.timeout))

    def collect(done) -> None:
        for future in done:
            accepted, failed = future.result()
            stats.accepted += accepted
            stats.failed += failed

    started = time.monotonic()
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        batch: list[dict[str, object]] = []
        for event in iter_events(path, args.event_type, args.source, args.limit):
            stats.rows += 1
            stats.emitted += 1
            batch.append(event)
            if len(batch) >= args.batch_size:
                submit_batch(executor, batch)
                batch = []
            while len(pending) >= args.workers * 2:
                done, pending = wait(pending, return_when=FIRST_COMPLETED)
                collect(done)
        submit_batch(executor, batch)
        if pending:
            done, pending = wait(pending)
            collect(done)
    elapsed = time.monotonic() - started
    print(
        f"file={path} rows={stats.rows} emitted={stats.emitted} "
        f"accepted={stats.accepted} failed={stats.failed} elapsed={elapsed:.3f}s",
        file=sys.stderr,
    )
    return stats


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", type=Path, help="Tableau Sample Superstore Orders CSV")
    parser.add_argument("-target", default="http://127.0.0.1:8088/ingest/json", help="qstream-loader JSON ingest endpoint")
    parser.add_argument("-batch-size", type=int, default=1000, help="events per loader POST")
    parser.add_argument("-workers", type=int, default=1, help="concurrent POST workers")
    parser.add_argument("-timeout", type=float, default=60.0, help="HTTP request timeout in seconds")
    parser.add_argument("-event-type", default="superstore_order", help="loader selector event type")
    parser.add_argument("-source", default="tableau-superstore-csv", help="event source label")
    parser.add_argument("-limit", type=int, default=0, help="maximum rows to emit; 0 means no limit")
    args = parser.parse_args()

    if args.batch_size <= 0:
        parser.error("-batch-size must be greater than zero")
    if args.workers <= 0:
        parser.error("-workers must be greater than zero")

    stats = load_csv(args.csv, args)
    if stats.failed:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
