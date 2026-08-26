#!/usr/bin/env python3
"""Convert QuantaStream MySQL command traces into SQLRunner draft suites."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Iterable

import summarize_mysql_trace as trace

QUERY_KEYWORDS = {"select", "show", "describe", "desc", "explain", "with"}
SKIPPED_SQL_PREFIXES = ("commit", "rollback")

PHASE_ORDER = ["connect", "metadata", "worksheet", "custom_sql", "extract"]
PHASE_SUITE_NAMES = {
    "connect": "mysql_compat_tableau_connect",
    "metadata": "mysql_compat_tableau_metadata",
    "worksheet": "mysql_compat_tableau_worksheets",
    "custom_sql": "mysql_compat_tableau_custom_sql",
    "extract": "mysql_compat_tableau_extract",
}
PHASE_FEATURES = {
    "connect": "tableau_connect_capture",
    "metadata": "tableau_metadata_capture",
    "worksheet": "tableau_worksheet_capture",
    "custom_sql": "tableau_custom_sql_capture",
    "extract": "tableau_extract_capture",
}
PHASE_REQUIRES = {
    "connect": "tableau_connect",
    "metadata": "tableau_metadata",
    "worksheet": "tableau_worksheet",
    "custom_sql": "tableau_custom_sql",
    "extract": "tableau_extract",
}


def load_events(paths: list[Path]) -> list[trace.TraceEvent]:
    if not paths:
        return list(trace.iter_events([]))
    events: list[trace.TraceEvent] = []
    for path in paths:
        if path.suffix.lower() in {".jsonl", ".ndjson"}:
            events.extend(load_events_jsonl(path))
        else:
            events.extend(trace.iter_events([path]))
    return events


def load_events_jsonl(path: Path) -> Iterable[trace.TraceEvent]:
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line_number, line in enumerate(handle, 1):
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            yield trace.TraceEvent(
                source=row.get("source", str(path)),
                line_number=int(row.get("line_number", line_number)),
                connection_id=str(row.get("connection_id", "")),
                user=str(row.get("user", "")),
                db=str(row.get("db", "")),
                kind=str(row.get("kind", "")),
                sql=str(row.get("sql", "")),
                statement_id=str(row.get("statement_id", "")),
                parameter_id=str(row.get("parameter_id", "")),
                long_data_bytes=str(row.get("long_data_bytes", "")),
                response=str(row.get("response", "")),
                elapsed=str(row.get("elapsed", "")),
                error=str(row.get("error", "")),
            )


def sqlrunner_kind(sql: str) -> str:
    keyword = first_keyword(sql)
    if keyword in QUERY_KEYWORDS:
        return "query"
    return "statement"


def first_keyword(sql: str) -> str:
    match = re.search(r"[A-Za-z_]+", sql.lstrip("( \t\r\n"))
    return match.group(0).lower() if match else "sql"


def sql_slug(sql: str) -> str:
    words = re.findall(r"[A-Za-z0-9_]+", trace.normalize_sql(sql).lower())
    words = [word for word in words if word not in {"select", "from", "where", "as", "the"}]
    slug = "_".join(words[:4]) or first_keyword(sql) or "sql"
    slug = re.sub(r"_+", "_", slug).strip("_")
    digest = hashlib.sha1(trace.normalize_sql(sql).encode("utf-8")).hexdigest()[:8]
    return f"{slug}_{digest}"


def should_skip_sql(sql: str) -> bool:
    normalized = trace.normalize_sql(sql).lower()
    return not normalized or any(normalized.startswith(prefix) for prefix in SKIPPED_SQL_PREFIXES)


def classify_sql(sql: str) -> str:
    normalized = trace.normalize_sql(sql)
    lowered = normalized.lower()
    keyword = first_keyword(normalized)

    if not lowered:
        return "worksheet"

    if is_connect_sql(lowered):
        return "connect"
    if is_metadata_sql(lowered, keyword):
        return "metadata"
    if is_extract_sql(lowered):
        return "extract"
    if is_custom_sql_wrapper(lowered):
        return "custom_sql"
    if keyword in QUERY_KEYWORDS:
        return "worksheet"
    return "connect"


def is_connect_sql(lowered_sql: str) -> bool:
    if lowered_sql.startswith("set ") or lowered_sql.startswith("use "):
        return True
    if lowered_sql in {"show warnings", "select 1", "select 1 as ping_value"}:
        return True
    if lowered_sql.startswith("select @@"):
        return True
    if lowered_sql.startswith("show variables"):
        return True
    if lowered_sql.startswith("show character set") or lowered_sql.startswith("show collation"):
        return True
    if lowered_sql.startswith("select database()") or lowered_sql.startswith("select schema()"):
        return True
    if lowered_sql.startswith("select version()") or lowered_sql.startswith("select user()"):
        return True
    if "connection_id()" in lowered_sql or "current_user()" in lowered_sql:
        return True
    return False


def is_metadata_sql(lowered_sql: str, keyword: str) -> bool:
    if "information_schema" in lowered_sql:
        return True
    if keyword in {"describe", "desc", "explain"}:
        return True
    metadata_show_prefixes = (
        "show databases",
        "show schemas",
        "show tables",
        "show full tables",
        "show table status",
        "show open tables",
        "show columns",
        "show full columns",
        "show fields",
        "show full fields",
        "show index",
        "show indexes",
        "show keys",
        "show create",
        "show engines",
        "show processlist",
        "show grants",
        "show privileges",
        "show function status",
        "show procedure status",
        "show triggers",
        "show events",
    )
    return lowered_sql.startswith(metadata_show_prefixes)


def is_extract_sql(lowered_sql: str) -> bool:
    if "tableauextract" in lowered_sql:
        return True
    if re.search(r"\bcount\s*\(\s*\*\s*\)\s+as\s+row_count\b", lowered_sql):
        return True
    return False


def is_custom_sql_wrapper(lowered_sql: str) -> bool:
    if "tableausql" in lowered_sql:
        return True
    return bool(re.search(r"\bfrom\s*\(", lowered_sql))


def unique_sql_events(events: list[trace.TraceEvent], include_errors: bool) -> list[trace.TraceEvent]:
    by_sql: dict[str, trace.TraceEvent] = {}
    for event in events:
        if event.kind not in {"query", "stmt_prepare"}:
            continue
        if not event.sql or should_skip_sql(event.sql):
            continue
        if event.response == "error" and not include_errors:
            continue
        key = trace.normalize_sql(event.sql).lower()
        by_sql.setdefault(key, event)
    return sorted(by_sql.values(), key=lambda event: (event.source, event.line_number, trace.normalize_sql(event.sql).lower()))


def group_events_by_phase(events: list[trace.TraceEvent], include_errors: bool) -> dict[str, list[trace.TraceEvent]]:
    grouped: dict[str, list[trace.TraceEvent]] = {phase: [] for phase in PHASE_ORDER}
    for event in unique_sql_events(events, include_errors=include_errors):
        grouped[classify_sql(event.sql)].append(event)
    return grouped


def render_suite(events: list[trace.TraceEvent], suite_name: str, feature: str, include_errors: bool, classify: bool = False) -> str:
    selected = unique_sql_events(events, include_errors=include_errors)
    lines: list[str] = []
    lines.append("# Generated by scripts/trace_to_sqlrunner.py.")
    lines.append("# Review IDs, features, and expected results before moving this into the QuantaStream engine repo.")
    lines.append("version: 1")
    lines.append(f"name: {suite_name}")
    lines.append("")
    lines.append("tests:")
    if not selected:
        lines.append("  []")
        return "\n".join(lines) + "\n"

    for index, event in enumerate(selected, 1):
        sql = trace.normalize_sql(event.sql)
        phase = classify_sql(sql) if classify else ""
        case_feature = PHASE_FEATURES[phase] if classify else feature
        requires = ["tableau_capture", PHASE_REQUIRES[phase]] if classify else ["tableau_capture"]
        case_id = f"{suite_name}.{index:03d}.{sql_slug(sql)}"
        response_error = event.response == "error"
        status = "xfail" if response_error else "supported"
        lines.append(f"  - id: {case_id}")
        lines.append(f"    status: {status}")
        lines.append(f"    kind: {sqlrunner_kind(sql)}")
        lines.append(f"    feature: {case_feature}")
        lines.append("    compatibility: mysql")
        lines.append(f"    requires: [{', '.join(requires)}]")
        lines.append("    sql: |")
        for sql_line in sql.splitlines() or [sql]:
            lines.append(f"      {sql_line}")
        if response_error:
            lines.append("    expect:")
            lines.append(f"      error: {yaml_scalar(event.error or 'error')}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_phase_suites(events: list[trace.TraceEvent], include_errors: bool) -> dict[str, str]:
    grouped = group_events_by_phase(events, include_errors=include_errors)
    rendered: dict[str, str] = {}
    for phase in PHASE_ORDER:
        phase_events = grouped[phase]
        if not phase_events:
            continue
        suite_name = PHASE_SUITE_NAMES[phase]
        rendered[f"{suite_name}.yaml"] = render_suite(
            phase_events,
            suite_name,
            PHASE_FEATURES[phase],
            include_errors=include_errors,
            classify=True,
        )
    return rendered


def write_phase_suites(events: list[trace.TraceEvent], out_dir: Path, include_errors: bool) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for filename, content in render_phase_suites(events, include_errors=include_errors).items():
        path = out_dir / filename
        path.write_text(content, encoding="utf-8")
        written.append(path)
    return written


def yaml_scalar(value: str) -> str:
    value = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{value}"'


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate SQLRunner draft suites from QS MYSQL_COMMAND_TRACE logs or events JSONL.")
    parser.add_argument("paths", nargs="*", type=Path, help="Trace log or events JSONL files. Reads stdin as trace log when omitted.")
    parser.add_argument("--suite-name", default="mysql_compat_tableau_capture")
    parser.add_argument("--feature", default="tableau_trace_replay")
    parser.add_argument("--classify", action="store_true", help="Classify each SQL statement as connect, metadata, worksheet, custom SQL, or extract.")
    parser.add_argument("--split-by-phase", action="store_true", help="Write one draft suite per Tableau phase. Requires --out-dir.")
    parser.add_argument("--include-errors", action="store_true", help="Include SQL commands that produced MySQL error responses as xfail cases.")
    parser.add_argument("--out", type=Path, help="Output YAML path for single-suite mode. Prints to stdout when omitted.")
    parser.add_argument("--out-dir", type=Path, help="Output directory for --split-by-phase mode.")
    args = parser.parse_args(argv)

    events = load_events(args.paths)
    if args.split_by_phase:
        if not args.out_dir:
            parser.error("--split-by-phase requires --out-dir")
        written = write_phase_suites(events, args.out_dir, include_errors=args.include_errors)
        for path in written:
            print(path)
        return 0

    suite = render_suite(events, args.suite_name, args.feature, args.include_errors, classify=args.classify)
    if args.out:
        args.out.write_text(suite, encoding="utf-8")
    else:
        sys.stdout.write(suite)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
