#!/usr/bin/env python3
"""Generate two synthetic bookmark HTML exports with overlapping entries.

The samples mimic a Chrome export and a Firefox export from the same
user: shared links (some with tracking parameters or a trailing slash
difference), one folder spelled differently ("News" vs "news"), one
empty folder, and one piece of malformed markup (an unclosed anchor).
No real browsing history is included. Run from the project root:

    python3 examples/make_samples.py
    python3 bookmarks_merge.py examples/chrome_bookmarks.html examples/firefox_bookmarks.html --out merged_bookmarks.html
"""

from pathlib import Path


def bookmark(url, title, add_date):
    return (
        '    <DT><A HREF="%s" ADD_DATE="%d">%s</A>\n' % (url, add_date, title)
    )


def folder(name, add_date, body):
    return (
        '    <DT><H3 ADD_DATE="%d">%s</H3>\n    <DL><p>\n%s    </DL><p>\n'
        % (add_date, name, body)
    )


def document(body):
    return (
        "<!DOCTYPE NETSCAPE-Bookmark-file-1>\n"
        '<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">\n'
        "<TITLE>Bookmarks</TITLE>\n<H1>Bookmarks</H1>\n<DL><p>\n"
        + body
        + "</DL><p>\n"
    )


CHROME = document(
    folder(
        "News",
        1700000000,
        bookmark("https://news.example.com/", "Example News", 1700000100)
        + bookmark(
            "https://news.example.com/story?utm_source=twitter&utm_medium=social",
            "Big Story",
            1700000200,
        )
        + bookmark("https://blog.example.com/post", "Old Post Title", 1700000300),
    )
    + folder("Tools", 1700000000, bookmark("https://tools.example.com/", "Tools Home", 1700000400))
    + folder("Empty Folder", 1700000000, "")
)

FIREFOX = document(
    folder(
        "news",
        1710000000,
        bookmark("https://news.example.com", "Example News", 1710000100)
        + bookmark(
            "https://news.example.com/story",
            "Big Story",
            1710000200,
        )
        + bookmark("https://blog.example.com/post/", "New Post Title", 1710000300),
    )
    + folder("Cooking", 1710000000, bookmark("https://recipes.example.com/pasta", "Pasta Night", 1710000400))
    # Malformed on purpose: an unclosed anchor at the end of the file.
    + '    <DT><A HREF="https://broken.example.com/page" ADD_DATE="1710000500">Broken Link\n'
)


def main():
    here = Path(__file__).resolve().parent
    (here / "chrome_bookmarks.html").write_text(CHROME, encoding="utf-8")
    (here / "firefox_bookmarks.html").write_text(FIREFOX, encoding="utf-8")
    print("wrote chrome_bookmarks.html, firefox_bookmarks.html")


if __name__ == "__main__":
    main()
