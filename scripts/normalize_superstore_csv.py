#!/usr/bin/env python3
"""Normalize Tableau Sample Superstore Orders CSV headers for QuantaStream.

This small helper reads a CSV exported from Tableau's Sample Superstore Orders
worksheet and writes a normalized CSV with snake_case headers that match
`configuration/superstore_orders/schema.yaml`.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

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


def normalize_header(header: str) -> str:
    return HEADER_MAP.get(header.strip(), header.strip().lower().replace(" ", "_"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Source Sample Superstore Orders CSV")
    parser.add_argument("output", type=Path, help="Normalized output CSV")
    args = parser.parse_args()

    with args.input.open(newline="", encoding="utf-8-sig") as src:
        reader = csv.DictReader(src)
        if not reader.fieldnames:
            raise SystemExit("input CSV has no header row")
        normalized = [normalize_header(name) for name in reader.fieldnames]
        missing = [name for name in REQUIRED_HEADERS if name not in normalized]
        if missing:
            raise SystemExit("missing required normalized headers: " + ", ".join(missing))

        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("w", newline="", encoding="utf-8") as dst:
            writer = csv.DictWriter(dst, fieldnames=REQUIRED_HEADERS, extrasaction="ignore")
            writer.writeheader()
            for row in reader:
                normalized_row = {normalize_header(k): v for k, v in row.items()}
                writer.writerow({name: normalized_row.get(name, "") for name in REQUIRED_HEADERS})

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
