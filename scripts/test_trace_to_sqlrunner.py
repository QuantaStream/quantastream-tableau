#!/usr/bin/env python3
from __future__ import annotations

import io
import json
import tempfile
import unittest
from pathlib import Path

import summarize_mysql_trace as trace
import trace_to_sqlrunner as replay


class TraceToSQLRunnerTests(unittest.TestCase):
    def test_generates_deduplicated_suite(self) -> None:
        events = list(trace.iter_stream_events(io.StringIO("\n".join([
            'MYSQL_COMMAND_TRACE connection_id=1 kind=query sql="show tables" response=query elapsed=1ms',
            'MYSQL_COMMAND_TRACE connection_id=1 kind=query sql="show   tables" response=query elapsed=1ms',
            'MYSQL_COMMAND_TRACE connection_id=1 kind=query sql="set sql_select_limit=1000" response=ok elapsed=1ms',
        ])), "stdin"))
        suite = replay.render_suite(events, "mysql_compat_tableau_capture", "tableau_trace_replay", include_errors=False)
        self.assertIn("version: 1", suite)
        self.assertIn("name: mysql_compat_tableau_capture", suite)
        self.assertEqual(suite.count("  - id:"), 2)
        self.assertIn("kind: query", suite)
        self.assertIn("kind: statement", suite)
        self.assertIn("show tables", suite)
        self.assertIn("set sql_select_limit=1000", suite)

    def test_skips_errors_by_default_and_can_include_them(self) -> None:
        events = list(trace.iter_stream_events(io.StringIO(
            'MYSQL_COMMAND_TRACE connection_id=1 kind=query sql="select bad" response=error elapsed=1ms error="parser_boundary"\n'
        ), "stdin"))
        self.assertNotIn("select bad", replay.render_suite(events, "suite", "feature", include_errors=False))
        suite = replay.render_suite(events, "suite", "feature", include_errors=True)
        self.assertIn("status: xfail", suite)
        self.assertIn("select bad", suite)
        self.assertIn('error: "parser_boundary"', suite)

    def test_reads_events_jsonl(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "events.jsonl"
            path.write_text(json.dumps({"source": "trace.log", "line_number": 2, "kind": "query", "sql": "select 1", "response": "query"}) + "\n", encoding="utf-8")
            events = list(replay.load_events([path]))
            self.assertEqual(events[0].sql, "select 1")


if __name__ == "__main__":
    unittest.main()
