#!/usr/bin/env python3
from __future__ import annotations

import unittest

import load_superstore_csv as loader


class SuperstoreLoaderTest(unittest.TestCase):
    def test_normalize_row_accepts_tableau_headers(self) -> None:
        row = {
            "Row ID": "1",
            "Order ID": "CA-2026-1",
            "Order Date": "1/2/2026",
            "Ship Date": "2026-01-05",
            "Ship Mode": "Second Class",
            "Customer ID": "CG-12520",
            "Customer Name": "Claire Gute",
            "Segment": "Consumer",
            "Country/Region": "United States",
            "City": "Henderson",
            "State/Province": "Kentucky",
            "Postal Code": "42420",
            "Region": "South",
            "Product ID": "FUR-BO-10001798",
            "Category": "Furniture",
            "Sub-Category": "Bookcases",
            "Product Name": "Bush Somerset Collection Bookcase",
            "Sales": "261.96",
            "Quantity": "2",
            "Discount": "0",
            "Profit": "41.9136",
        }
        got = loader.normalize_row(row)
        self.assertEqual(got["row_id"], 1)
        self.assertEqual(got["order_date"], "2026-01-02")
        self.assertEqual(got["ship_date"], "2026-01-05")
        self.assertEqual(got["quantity"], 2)
        self.assertEqual(got["sales"], 261.96)
        self.assertEqual(got["country_region"], "United States")
        self.assertEqual(got["sub_category"], "Bookcases")

    def test_event_shape_matches_loader_selector(self) -> None:
        data = {name: "x" for name in loader.REQUIRED_HEADERS}
        data["row_id"] = 42
        data["order_id"] = "CA-2026-42"
        data["order_date"] = "2026-01-02"
        event = loader.event_for_row(data, "superstore_order", "unit-test")
        self.assertEqual(event["mode"], "batch")
        self.assertEqual(event["event_id"], "superstore.order.42")
        self.assertEqual(event["event_time"], "2026-01-02T00:00:00Z")
        self.assertEqual(event["payload"]["type"], "superstore_order")
        self.assertEqual(event["payload"]["data"], data)
        self.assertEqual(event["shard_key"], "superstore.order.CA-2026-42")


if __name__ == "__main__":
    unittest.main()
