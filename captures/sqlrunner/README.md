# SQLRunner Replay Notes

This directory is a holding area for Tableau SQL that should become SQLRunner
compatibility suites in the QuantaStream engine repository.

Generate a first-pass suite from a QS command trace log:

```bash
scripts/trace_to_sqlrunner.py /tmp/quantastream-tableau.log \
  --classify \
  > captures/sqlrunner/mysql_compat_tableau_capture.yaml
```

Or generate from parsed events JSONL emitted by `summarize_mysql_trace.py`:

```bash
scripts/trace_to_sqlrunner.py captures/tableau-desktop-smoke-events.jsonl \
  --suite-name mysql_compat_tableau_metadata \
  > captures/sqlrunner/mysql_compat_tableau_metadata.yaml
```

The generated YAML is intentionally a draft. Use `--classify` for one suite
with per-case Tableau phase metadata, or use `--split-by-phase --out-dir ...`
to emit separate connect, metadata, worksheet, custom SQL, and extract drafts.
Review IDs and add expected rows or expected errors before moving generated SQL
into the engine repo.

Proposed engine-suite names:

- `mysql_compat_tableau_connect.yaml`
- `mysql_compat_tableau_metadata.yaml`
- `mysql_compat_tableau_worksheets.yaml`
- `mysql_compat_tableau_custom_sql.yaml`
- `mysql_compat_tableau_extract.yaml`

Keep this directory lightweight. The executable suites belong in the engine repo
once the SQL is cleaned and expected results are known. Regression fixtures for
this conversion pipeline live under `fixtures/`.
