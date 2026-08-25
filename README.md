# QuantaStream Tableau

This repository contains Tableau integration assets for QuantaStream.

The first integration target is Tableau Desktop using Tableau's native MySQL
connector against the QuantaStream MySQL-compatible endpoint. The goal is to
make Tableau connect, browse schemas, preview rows, run worksheets, exercise
custom SQL, and eventually validate extract behavior against realistic
QuantaStream data sets.

## Scope

Planned contents include:

- Tableau connection and smoke-test runbooks;
- captured Tableau-generated SQL;
- SQLRunner replay suites for Tableau compatibility;
- sample dashboards or workbook assets built from QuantaStream sample data;
- Tableau Datasource Verification Tool notes and results;
- connector experiments if a dedicated Tableau connector becomes useful later.

This repository should not contain QuantaStream engine code, Tableau binaries,
private customer data, or unsanitized connection logs.

## Licensing

The contents of this repository are licensed under the Apache License 2.0. See
[LICENSE](LICENSE).

QuantaStream itself is licensed separately under the Elastic License 2.0. This
repository is intentionally focused on integration assets, examples, and
compatibility harnesses rather than the core database engine.

## Status

This repository is new. The current development plan lives internally while the
Tableau compatibility surface is being explored.

Near-term engineering path:

1. Capture real Tableau Desktop SQL traffic against a local QuantaStream server.
2. Convert captured traffic into SQLRunner replay suites.
3. Harden metadata, worksheet, custom SQL, and extract behavior based on those
   captures.
4. Use Tableau's verification tooling later as an external compatibility
   pressure test.

## Related Repositories

- [QuantaStream](https://github.com/QuantaStream/quantastream)
- [QuantaStream website](https://github.com/QuantaStream/QuantaStream.github.io)

