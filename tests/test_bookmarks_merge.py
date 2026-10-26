"""Tests for bookmarks_merge. All fixtures are inline or synthetic."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import bookmarks_merge as bm


def write(tmp_path, name, text):
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return str(path)


def doc(body):
    return (
        "<!DOCTYPE NETSCAPE-Bookmark-file-1>\n"
        "<TITLE>Bookmarks</TITLE>\n<H1>Bookmarks</H1>\n<DL><p>\n"
        + body
        + "</DL><p>\n"
    )


def link(url, title="T", date=None):
    date_attr = ' ADD_DATE="%d"' % date if date is not None else ""
    return '<DT><A HREF="%s"%s>%s</A>\n' % (url, date_attr, title)


def folder(name, body, date=None):
    date_attr = ' ADD_DATE="%d"' % date if date is not None else ""
    return '<DT><H3%s>%s</H3>\n<DL><p>\n%s</DL><p>\n' % (date_attr, name, body)


# URL normalization


def test_trailing_slash_and_root_slash_match():
    assert bm.normalize_url("https://example.com/") == bm.normalize_url(
        "https://example.com"
    )
    assert bm.normalize_url("https://example.com/page/") == bm.normalize_url(
        "https://example.com/page"
    )


def test_utm_and_tracking_params_dropped():
    assert bm.normalize_url(
        "https://example.com/s?utm_source=x&utm_medium=y&a=1"
    ) == bm.normalize_url("https://example.com/s?a=1")
    assert bm.normalize_url("https://example.com/s?fbclid=abc") == bm.normalize_url(
        "https://example.com/s"
    )


def test_query_order_ignored_but_fragment_kept():
    assert bm.normalize_url("https://example.com/s?b=2&a=1") == bm.normalize_url(
        "https://example.com/s?a=1&b=2"
    )
    assert bm.normalize_url("https://example.com/s#top") != bm.normalize_url(
        "https://example.com/s#bottom"
    )


def test_host_case_and_default_port_dropped():
    assert bm.normalize_url("HTTP://EXAMPLE.COM:80/x") == bm.normalize_url(
        "http://example.com/x"
    )
    assert bm.normalize_url("https://example.com:443/x") == bm.normalize_url(
        "https://example.com/x"
    )


def test_www_kept_distinct():
    assert bm.normalize_url("https://www.example.com/") != bm.normalize_url(
        "https://example.com/"
    )


def test_non_absolute_url_compared_verbatim():
    assert bm.normalize_url("javascript:void(0)") == "javascript:void(0)"
    assert bm.normalize_url("/relative/path") == "/relative/path"


# Parsing


def test_parse_folders_and_root_bookmarks():
    root, errors = bm.parse_bookmarks(
        doc(link("https://a.example.com", "Root Link") + folder("News", link("https://b.example.com", "News Link")))
    )
    assert errors == []
    assert len(root.children) == 2
    assert root.children[0].url == "https://a.example.com"
    news = root.children[1]
    assert news.name == "News"
    assert news.children[0].url == "https://b.example.com"


def test_parse_nested_folders():
    root, _ = bm.parse_bookmarks(doc(folder("Outer", folder("Inner", link("https://x.example.com")))))
    assert root.children[0].children[0].name == "Inner"


def test_parse_malformed_html_is_graceful():
    broken = doc(link("https://a.example.com", "Open") + "<DT><A HREF=\"https://b.example.com\"")
    root, errors = bm.parse_bookmarks(broken)
    bookmarks, _folders = bm.count_tree(root)
    assert bookmarks == 2


def test_parse_add_date():
    root, _ = bm.parse_bookmarks(doc(link("https://a.example.com", "T", date=1700000000)))
    assert root.children[0].add_date == 1700000000


# Merging


def test_folders_merge_case_insensitively():
    a, _ = bm.parse_bookmarks(doc(folder("News", link("https://a.example.com"))))
    b, _ = bm.parse_bookmarks(doc(folder("news", link("https://b.example.com"))))
    merged, dups = bm.merge_trees([("a", a), ("b", b)])
    assert len(merged.children) == 1
    assert merged.children[0].name == "News"
    assert len(merged.children[0].children) == 2
    assert dups == []


def test_duplicate_url_dropped_first_wins():
    a, _ = bm.parse_bookmarks(doc(link("https://example.com/", "First", date=100)))
    b, _ = bm.parse_bookmarks(doc(link("https://example.com", "Second", date=200)))
    merged, dups = bm.merge_trees([("a", a), ("b", b)])
    assert len(merged.children) == 1
    assert merged.children[0].title == "First"
    assert len(dups) == 1
    assert dups[0]["kept_title"] == "First"
    assert dups[0]["dropped_title"] == "Second"


def test_keep_newest_replaces_title_and_date():
    a, _ = bm.parse_bookmarks(doc(link("https://example.com", "Old", date=100)))
    b, _ = bm.parse_bookmarks(doc(link("https://example.com/", "New", date=200)))
    merged, dups = bm.merge_trees(
        [("a", a), ("b", b)], keep_newest=True
    )
    assert merged.children[0].title == "New"
    assert merged.children[0].add_date == 200
    assert dups[0]["kept_updated"] is True


def test_keep_newest_ignores_older_duplicate():
    a, _ = bm.parse_bookmarks(doc(link("https://example.com", "New", date=200)))
    b, _ = bm.parse_bookmarks(doc(link("https://example.com/", "Old", date=100)))
    merged, _dups = bm.merge_trees([("a", a), ("b", b)], keep_newest=True)
    assert merged.children[0].title == "New"


def test_no_dedup_keeps_everything():
    a, _ = bm.parse_bookmarks(doc(link("https://example.com/")))
    b, _ = bm.parse_bookmarks(doc(link("https://example.com")))
    merged, dups = bm.merge_trees([("a", a), ("b", b)], dedup=False)
    assert len(merged.children) == 2
    assert dups == []


def test_flatten_removes_empty_folders():
    a, _ = bm.parse_bookmarks(doc(folder("Empty", "") + folder("Full", link("https://a.example.com"))))
    merged, _ = bm.merge_trees([("a", a)])
    removed = bm.flatten_empty_folders(merged)
    assert removed == 1
    assert [c.name for c in merged.children] == ["Full"]


def test_flatten_removes_nested_empty_chain():
    a, _ = bm.parse_bookmarks(doc(folder("Outer", folder("Inner", ""))))
    merged, _ = bm.merge_trees([("a", a)])
    assert bm.flatten_empty_folders(merged) == 2
    assert merged.children == []


# Rendering and round trip


def test_rendered_output_reparses_to_same_links():
    a, _ = bm.parse_bookmarks(doc(folder("News", link("https://a.example.com", "A", date=123))))
    merged, _ = bm.merge_trees([("a", a)])
    out = bm.render_html(merged)
    assert out.startswith("<!DOCTYPE NETSCAPE-Bookmark-file-1>")
    again, _ = bm.parse_bookmarks(out)
    assert again.children[0].name == "News"
    assert again.children[0].children[0].url == "https://a.example.com"
    assert again.children[0].children[0].add_date == 123


def test_render_escapes_html():
    # A literal <B> inside an anchor is markup to a real HTML parser, so
    # test escaping with plain ampersands, which do survive parsing.
    a, _ = bm.parse_bookmarks(doc(link("https://example.com/?a=1&b=2", "Fish & Chips")))
    merged, _ = bm.merge_trees([("a", a)])
    out = bm.render_html(merged)
    assert "Fish &amp; Chips" in out
    assert "a=1&amp;b=2" in out


# CLI behaviour


def test_cli_merges_and_writes(tmp_path):
    first = write(tmp_path, "a.html", doc(link("https://a.example.com", "A")))
    second = write(tmp_path, "b.html", doc(link("https://b.example.com", "B")))
    out = str(tmp_path / "merged.html")
    assert bm.main([first, second, "--out", out]) == 0
    merged, _ = bm.parse_bookmarks(Path(out).read_text(encoding="utf-8"))
    assert [c.url for c in merged.children] == [
        "https://a.example.com",
        "https://b.example.com",
    ]


def test_cli_check_exit_codes(tmp_path):
    first = write(tmp_path, "a.html", doc(link("https://example.com/", "A")))
    second = write(tmp_path, "b.html", doc(link("https://example.com", "B")))
    assert bm.main([first, second, "--check"]) == 1
    assert bm.main([first, "--check"]) == 0


def test_cli_dry_run_writes_nothing(tmp_path):
    first = write(tmp_path, "a.html", doc(link("https://a.example.com")))
    out = str(tmp_path / "merged.html")
    assert bm.main([first, "--dry-run", "--out", out]) == 0
    assert not Path(out).exists()


def test_cli_json_report(tmp_path, capsys):
    first = write(tmp_path, "a.html", doc(link("https://example.com/", "A")))
    second = write(tmp_path, "b.html", doc(link("https://example.com", "B")))
    assert bm.main([first, second, "--json"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["merged_bookmarks"] == 1
    assert report["duplicates_dropped"] == 1
    assert report["inputs"][0]["bookmarks"] == 1


def test_cli_report_file_and_missing_input(tmp_path):
    first = write(tmp_path, "a.html", doc(link("https://a.example.com")))
    report_path = str(tmp_path / "report.json")
    assert bm.main([first, "--report", report_path]) == 0
    report = json.loads(Path(report_path).read_text(encoding="utf-8"))
    assert report["merged_bookmarks"] == 1
    assert bm.main([str(tmp_path / "nope.html")]) == 2
    assert bm.main([]) == 2
