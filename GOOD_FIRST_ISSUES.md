# Good first issues

Seeded ideas for new contributors. Each one is small, tested, and safe
to take: open an issue or a pull request against this file's text.

## 1. Preserve the bookmark toolbar folder flag

Problem: browsers mark the bookmarks bar with
`PERSONAL_TOOLBAR_FOLDER="true"` on its H3, and the merge drops that
attribute, so an imported file loses the toolbar distinction. Work:
carry the attribute through the Folder node, keep it on merge when
either source folder has it, and render it on the merged H3. Files:
bookmarks_merge.py (parser, Folder, renderer),
tests/test_bookmarks_merge.py, README.md (limitations section).
Tests to add: toolbar flag survives a merge, flag from either side
wins, non-toolbar folders stay unflagged.

## 2. Add a --report-duplicates text listing

Problem: the dropped duplicates are only visible in `--json` output,
so a user running the plain merge cannot see which links were
removed. Work: after the merged summary line, print one line per
dropped duplicate (dropped title, kept title, folder) when duplicates
exist, capped at a readable count with a "and N more, see --json"
tail. Files: bookmarks_merge.py (text output in main),
tests/test_bookmarks_merge.py, README.md. Tests to add: duplicate
lines appear in plain output, the cap message appears with many
duplicates, `--json` output is unchanged.

## 3. Support Safari Reading List and Firefox JSON backups as inputs

Problem: only Netscape HTML exports are accepted, so users with a
Safari plist or a Firefox `.jsonlz4`/`.json` backup must export HTML
first. Work: accept Firefox JSON bookmark backups (the `children`
tree format) as an input type, detected by file content, and convert
them to the same Folder tree before merging. Keep HTML parsing
unchanged. Files: bookmarks_merge.py (new input reader),
tests/test_bookmarks_merge.py, README.md. Tests to add: JSON backup
parses to the same tree shape, HTML and JSON inputs merge together,
a malformed JSON file reports a parse error instead of crashing.

## 4. Add a --sort option for folders and bookmarks

Problem: merged output preserves first-seen order, which keeps two
users' messy orderings intact. Work: add `--sort`, which sorts
folders and bookmarks alphabetically (case-insensitive, folders
before bookmarks) at every level before writing, without changing
the dedupe result. Files: bookmarks_merge.py (sort step),
tests/test_bookmarks_merge.py, README.md (flags table). Tests to
add: sorted output order matches expectations, nested folders sort
too, unsorted output is unchanged without the flag.
