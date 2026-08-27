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
  --classify \
  > captures/sqlrunner/mysql_compat_tableau_capture.yaml

# Split captured SQL into connect, metadata, worksheet, custom SQL, and extract drafts:
scripts/trace_to_sqlrunner.py /tmp/quantastream-tableau.log \
  --split-by-phase \
  --out-dir captures/sqlrunner/generated

# Include failing SQL as xfail cases when triaging compatibility gaps:
scripts/trace_to_sqlrunner.py /tmp/quantastream-tableau.log \
  --classify \
  --include-errors \
  > captures/sqlrunner/mysql_compat_tableau_capture_with_gaps.yaml
```

Review summaries and generated suites before committing. Keep only sanitized,
useful captures. The sanitized fixture under `fixtures/tableau_trace_sanitized.log`
provides a small regression sample for the summary and suite-generation tools.

## Support Bundles

For QuantaStream engine issues triggered from Tableau, create a QS support
bundle and pass the Tableau trace log as a log path:

```bash
./bin/qstream-admin support bundle \
  --output /tmp/qstream-tableau-support-$(date -u +%Y%m%dT%H%M%SZ).tar.gz \
  --data-dir ./data \
  --config-dir ./runtime/config \
  --wal-path ./data/storage.wal \
  --auth-account-file ./auth/accounts.yaml \
  --access-policy-file ./auth/access-policy.yaml \
  --log-path /tmp/quantastream-tableau.log
```

The support bundle intentionally excludes table data files and raw auth/access
files, but it can include recent log tails. Review those log excerpts before
sharing. Tableau Desktop's own logs are separate; include only short sanitized
snippets when the QS trace does not explain the failure.

## Suggested Capture Names

Use descriptive names that identify the test phase and date, for example:

- `tableau-connect-20260825-summary.md`
- `tableau-metadata-20260825-events.jsonl`
- `tableau-worksheet-superstore-20260825-summary.md`
