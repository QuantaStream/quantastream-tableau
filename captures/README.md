# Tableau SQL Captures

Store sanitized Tableau-generated SQL captures here.

Do not commit private credentials, customer data, local machine names, or raw
logs containing secrets. Prefer small Markdown notes that describe:

- Tableau version;
- QuantaStream version;
- connector path;
- dataset;
- user action;
- SQL emitted;
- observed result;
- classification: supported, QS bug, unsupported SQL, Tableau setup issue.

Captured SQL that becomes stable compatibility coverage should be moved into the
QuantaStream engine repo as SQLRunner suites.
