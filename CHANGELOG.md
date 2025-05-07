# Changelog

## [v2025.05.07-v0.1] - 2025-05-07

### Added
- Unified fuzzy and exact reference matches under match type A
- Simplified match type system to A–E bands
- Cleaned up summary reporting with A–E aligned labels
- Prioritized raw industry match over keyword sector inference
- Added support for clean CSV export with only trusted columns
- Ignored output_data/ via .gitignore
- Introduced optional `--limit` flag for partial test runs

### Removed
- Fuzzy-specific summary reporting
- Scored_Leads.csv (replaced with scored_output_clean.csv)

### Fixed
- Cases where keyword matches overrode correct industry matches
- Misalignment between match_type and match_source