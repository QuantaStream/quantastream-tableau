#!/usr/bin/env python3
"""Summarize opt-in QuantaStream MySQL command trace logs.

The QS engine emits one trace line per decoded MySQL command when started with
`--mysql-command-trace` or `QUANTASTREAM_MYSQL_COMMAND_TRACE=true`. This helper
turns those lines into an inventory of command kinds, responses, errors, and
unique SQL text for Tableau compatibility work.
"""

from __future__ import annotations

import argparse
import collections
import json
import shlex
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable

TRACE_MARKER = "MYSQL_COMMAND_TRACE"


@dataclass(frozen=True)
class TraceEvent:
    source: str
    line_number: int
    connection_id: str = ""
    user: str = ""
    db: str = ""
    kind: str = ""
    sql: str = ""
    statement_id: str = ""
    parameter_id: str = ""
    long_data_bytes: str = ""
    response: str = ""
    elapsed: str = ""
    error: str = ""


def extract_trace_message(line: str) -> str | None:
    if TRACE_MARKER not in line:
        return None

    msg = extract_logfmt_msg(line)
    if msg and TRACE_MARKER in msg:
        marker_index = msg.find(TRACE_MARKER)
        return msg[marker_index:]

    marker_index = line.find(TRACE_MARKER)
    return line[marker_index:].strip().replace('\\"', '"')


def extract_logfmt_msg(line: str) -> str | None:
    marker = 'msg="'
    start = line.find(marker)
    if start == -1:
        return None
    start += len(marker)
    chars: list[str] = []
    escaped = False
    for char in line[start:]:
        if escaped:
            chars.append(char)
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char == '"':
            break
        chars.append(char)
    return "".join(chars)


def parse_trace_message(message: str, source: str, line_number: int) -> TraceEvent | None:
    try:
        tokens = shlex.split(message)
    except ValueError:
        return None
    if not tokens or tokens[0] != TRACE_MARKER:
        return None

    fields: dict[str, str] = {}
    for token in tokens[1:]:
        key, sep, value = token.partition("=")
        if sep:
            fields[key] = value

    return TraceEvent(
        source=source,
        line_number=line_number,
        connection_id=fields.get("connection_id", ""),
        user=fields.get("user", ""),
        db=fields.get("db", ""),
        kind=fields.get("kind", ""),
        sql=fields.get("sql", ""),
        statement_id=fields.get("statement_id", ""),
        parameter_id=fields.get("parameter_id", ""),
        long_data_bytes=fields.get("long_data_bytes", ""),
        response=fields.get("response", ""),
        elapsed=fields.get("elapsed", ""),
        error=fields.get("error", ""),
    )


def iter_events(paths: list[Path]) -> Iterable[TraceEvent]:
    if not paths:
        yield from iter_stream_events(sys.stdin, "<stdin>")
        return
    for path in paths:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            yield from iter_stream_events(handle, str(path))


def iter_stream_events(lines: Iterable[str], source: str) -> Iterable[TraceEvent]:
    for line_number, line in enumerate(lines, 1):
        message = extract_trace_message(line)
        if not message:
            continue
        event = parse_trace_message(message, source, line_number)
        if event:
            yield event


def normalize_sql(sql: str) -> str:
    return " ".join(sql.split())


def summarize(events: list[TraceEvent]) -> dict[str, object]:
    by_kind = collections.Counter(event.kind or "<missing>" for event in events)
    by_response = collections.Counter(event.response or "<missing>" for event in events)
    by_error = collections.Counter(event.error for event in events if event.error)
    by_sql = collections.Counter(normalize_sql(event.sql) for event in events if event.sql)
    by_kind_sql = collections.defaultdict(collections.Counter)
    for event in events:
        if event.sql:
            by_kind_sql[event.kind or "<missing>"][normalize_sql(event.sql)] += 1

    return {
        "event_count": len(events),
        "by_kind": dict(sorted(by_kind.items())),
        "by_response": dict(sorted(by_response.items())),
        "by_error": dict(by_error.most_common()),
        "unique_sql_count": len(by_sql),
        "top_sql": [{"count": count, "sql": sql} for sql, count in by_sql.most_common()],
        "top_sql_by_kind": {
            kind: [{"count": count, "sql": sql} for sql, count in counter.most_common()]
            for kind, counter in sorted(by_kind_sql.items())
        },
    }


def markdown_report(summary: dict[str, object], sql_limit: int) -> str:
    lines: list[str] = []
    lines.append("# MySQL Command Trace Summary")
    lines.append("")
    lines.append(f"Events: {summary['event_count']}")
    lines.append(f"Unique SQL statements: {summary['unique_sql_count']}")
    lines.append("")
    lines.extend(markdown_counter_table("Command Kind", summary["by_kind"]))
    lines.append("")
    lines.extend(markdown_counter_table("Response", summary["by_response"]))

    errors = summary["by_error"]
    if errors:
        lines.append("")
        lines.extend(markdown_counter_table("Errors", errors))

    top_sql = summary["top_sql"][:sql_limit]
    if top_sql:
        lines.append("")
        lines.append("## Top SQL")
        lines.append("")
        lines.append("| Count | SQL |")
        lines.append("| ---: | --- |")
        for row in top_sql:
            lines.append(f"| {row['count']} | `{escape_markdown_table(str(row['sql']))}` |")

    return "\n".join(lines) + "\n"


def markdown_counter_table(title: str, counter: dict[str, int]) -> list[str]:
    lines = [f"## {title}", "", "| Value | Count |", "| --- | ---: |"]
    for value, count in counter.items():
        lines.append(f"| `{escape_markdown_table(value)}` | {count} |")
    return lines


def escape_markdown_table(value: str) -> str:
    return value.replace("|", "\\|").replace("`", "\\`")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Summarize QuantaStream MYSQL_COMMAND_TRACE logs.")
    parser.add_argument("paths", nargs="*", type=Path, help="Trace log files. Reads stdin when omitted.")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    parser.add_argument("--sql-limit", type=int, default=30, help="Maximum SQL rows in the Markdown summary.")
    parser.add_argument("--events-jsonl", type=Path, help="Optional path to write parsed events as JSONL.")
    args = parser.parse_args(argv)

    events = list(iter_events(args.paths))
    if args.events_jsonl:
        with args.events_jsonl.open("w", encoding="utf-8") as handle:
            for event in events:
                handle.write(json.dumps(asdict(event), sort_keys=True) + "\n")

    summary = summarize(events)
    if args.format == "json":
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(markdown_report(summary, args.sql_limit), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
