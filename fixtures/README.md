# Fixtures

This directory contains sanitized command-trace fixtures and expected outputs
used by the Tableau helper tests.

- `tableau_trace_sanitized.log` is a tiny synthetic QS `MYSQL_COMMAND_TRACE`
  sample with connect, metadata, worksheet, custom SQL, extract, and xfail
  shapes.
- `tableau_trace_summary.md` is the expected Markdown summary for that trace.
- `sqlrunner/` contains expected SQLRunner YAML generated from the same trace,
  both as a single classified draft and as split-by-phase drafts.

Do not place real unsanitized Tableau logs, credentials, customer data, or local
environment details here.
