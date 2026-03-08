# Changelog

## 1.0.0 (2026-03-08)

### Added
- End-to-end PubWatch example pipeline (vision → epic decomposition → feature stabilization → OpenSpec export → implementation).
- PubWatch demo package (`examples/pubwatch/pubwatch`) with CLI entrypoint and SQLite persistence.

### Changed
- PubWatch PubMed fetching now parses real `efetch` XML responses (replaces earlier stub/sample paper data).

### Fixed
- OpenPlan integration/test fixes leading to a fully passing test suite.
