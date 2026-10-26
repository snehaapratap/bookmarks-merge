# Changelog

## v1.0.0 (2026-10-26)

- Initial release: merge any number of Netscape bookmark HTML exports
  (Chrome, Firefox, Safari, Edge) into one clean file that re-imports
  into any browser.
- Folder merge by path with case-insensitive name matching, keeping
  first-seen spelling and order.
- Global bookmark dedupe by normalized URL: scheme/host lowercased,
  default ports and trailing slashes dropped, utm_*/fbclid/gclid
  parameters dropped, remaining query parameters sorted, fragments
  kept, www. kept distinct.
- `--dedup` (default on) / `--no-dedup`, `--keep-newest`,
  `--flatten`, `--check` (exit 1 on duplicates or parse failure),
  `--dry-run`, `--json` and `--report` output.
- Tolerant html.parser based parsing: unclosed tags, stray text and
  missing DL wrappers are handled, with per-file bookmark and folder
  counts reported.
- 24 tests, all passing.
