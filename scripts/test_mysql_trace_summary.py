#!/usr/bin/env python3
from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

import summarize_mysql_trace as trace

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures"


class MySQLTraceSummaryTests(unittest.TestCase):
    def test_parses_raw_trace_line(self) -> None:
        line = 'MYSQL_COMMAND_TRACE connection_id=7 user="bench" db="quanta" kind=query sql="select * from t" response=ok elapsed=2ms'
        message = trace.extract_trace_message(line)
        self.assertEqual(message, line)
        event = trace.parse_trace_message(message or "", "raw.log", 1)
        self.assertIsNotNone(event)
        assert event is not None
        self.assertEqual(event.connection_id, "7")
        self.assertEqual(event.user, "bench")
        self.assertEqual(event.sql, "select * from t")
        self.assertEqual(event.response, "ok")

    def test_parses_logrus_wrapped_trace_line(self) -> None:
        line = r'time="2026-08-25T12:00:00Z" level=info msg="MYSQL_COMMAND_TRACE connection_id=8 user=\"qstream\" db=\"quanta\" kind=query sql=\"show tables\" response=query elapsed=1.2ms"'
        message = trace.extract_trace_message(line)
        self.assertEqual(message, 'MYSQL_COMMAND_TRACE connection_id=8 user="qstream" db="quanta" kind=query sql="show tables" response=query elapsed=1.2ms')
        event = trace.parse_trace_message(message or "", "engine.log", 5)
        self.assertIsNotNone(event)
        assert event is not None
        self.assertEqual(event.user, "qstream")
        self.assertEqual(event.sql, "show tables")
        self.assertEqual(event.response, "query")

    def test_summarizes_unique_sql_and_errors(self) -> None:
        lines = io.StringIO("\n".join([
            'MYSQL_COMMAND_TRACE connection_id=1 kind=query sql="select  *   from t" response=query elapsed=1ms',
            'MYSQL_COMMAND_TRACE connection_id=1 kind=query sql="select * from t" response=query elapsed=1ms',
            'MYSQL_COMMAND_TRACE connection_id=1 kind=decode_error response=error elapsed=1ms error="unsupported mysql command byte 0xff"',
        ]))
        events = list(trace.iter_stream_events(lines, "stdin"))
        summary = trace.summarize(events)
        self.assertEqual(summary["event_count"], 3)
        self.assertEqual(summary["unique_sql_count"], 1)
        self.assertEqual(summary["by_kind"], {"decode_error": 1, "query": 2})
        self.assertEqual(summary["by_response"], {"error": 1, "query": 2})
        report = trace.markdown_report(summary, sql_limit=5)
        self.assertIn("unsupported mysql command byte", report)
        self.assertIn("select * from t", report)

    def test_main_can_write_events_jsonl(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "trace.log"
            out = Path(tmp) / "events.jsonl"
            log.write_text('MYSQL_COMMAND_TRACE connection_id=1 kind=query sql="select 1" response=query elapsed=1ms\n', encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                rc = trace.main([str(log), "--format", "json", "--events-jsonl", str(out)])
            self.assertEqual(rc, 0)
            rows = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(rows[0]["sql"], "select 1")

    def test_sanitized_fixture_summary_stays_stable(self) -> None:
        self.maxDiff = None
        events = list(trace.iter_events([FIXTURES / "tableau_trace_sanitized.log"]))
        summary = trace.markdown_report(trace.summarize(events), sql_limit=20)
        expected = (FIXTURES / "tableau_trace_summary.md").read_text(encoding="utf-8")
        self.assertEqual(summary, expected)


if __name__ == "__main__":
    unittest.main()
