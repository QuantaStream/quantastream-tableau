# Captures

This directory is for sanitized Tableau-generated SQL captures and summaries.
Do not commit credentials, customer data, unsanitized engine logs, or screenshots
that expose private environment details.

## MySQL Command Trace Workflow

Start QuantaStream with command tracing enabled:

```bash
QUANTASTREAM_MYSQL_COMMAND_TRACE=true ./bin/quantastream \
  -config-dir ./runtime/config \
  -data-dir ./data \
  -wal-path ./data/storage.wal \
  -bind 127.0.0.1 \
  -mysql-port 4000 \
  -native-grpc-bind 127.0.0.1 \
  -native-grpc-port 4100 \
  -database quanta \
  -auth-mode static \
  -auth-account-file ./auth/accounts.yaml \
  -access-policy-file ./auth/access-policy.yaml \
  2>&1 | tee /tmp/quantastream-tableau.log
```

After a Tableau Desktop session, summarize the command trace:

```bash
scripts/summarize_mysql_trace.py /tmp/quantastream-tableau.log \
  > captures/tableau-desktop-smoke-summary.md

scripts/summarize_mysql_trace.py /tmp/quantastream-tableau.log \
  --format json \
  --events-jsonl captures/tableau-desktop-smoke-events.jsonl \
  > captures/tableau-desktop-smoke-summary.json
```

Generate a draft SQLRunner replay suite from the same trace:

```bash
scripts/trace_to_sqlrunner.py /tmp/quantastream-tableau.log \
  > captures/sqlrunner/mysql_compat_tableau_capture.yaml

# Include failing SQL as xfail cases when triaging compatibility gaps:
scripts/trace_to_sqlrunner.py /tmp/quantastream-tableau.log \
  --include-errors \
  > captures/sqlrunner/mysql_compat_tableau_capture_with_gaps.yaml
```

Review summaries and generated suites before committing. Keep only sanitized,
useful captures.

## Suggested Capture Names

Use descriptive names that identify the test phase and date, for example:

- `tableau-connect-20260825-summary.md`
- `tableau-metadata-20260825-events.jsonl`
- `tableau-worksheet-superstore-20260825-summary.md`
