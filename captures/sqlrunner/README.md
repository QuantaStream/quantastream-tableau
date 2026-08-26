# SQLRunner Replay Notes

This directory is a holding area for Tableau SQL that should become SQLRunner
compatibility suites in the QuantaStream engine repository.

Generate a first-pass suite from a QS command trace log:

```bash
scripts/trace_to_sqlrunner.py /tmp/quantastream-tableau.log \
  > captures/sqlrunner/mysql_compat_tableau_capture.yaml
```

Or generate from parsed events JSONL emitted by `summarize_mysql_trace.py`:

```bash
scripts/trace_to_sqlrunner.py captures/tableau-desktop-smoke-events.jsonl \
  --suite-name mysql_compat_tableau_metadata \
  > captures/sqlrunner/mysql_compat_tableau_metadata.yaml
```

The generated YAML is intentionally a draft. Review the IDs, split cases into
connect/metadata/worksheet suites, and add expected rows or expected errors
before moving it into the engine repo.

Proposed engine-suite names:

- `mysql_compat_tableau_connect.yaml`
- `mysql_compat_tableau_metadata.yaml`
- `mysql_compat_tableau_worksheets.yaml`
- `mysql_compat_tableau_custom_sql.yaml`

Keep this directory lightweight. The executable suites belong in the engine repo
once the SQL is cleaned and expected results are known.
