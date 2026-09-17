#!/usr/bin/env python3
"""Post-deploy live verification for homesteadcalc.com (Cloudflare Pages clean URLs).

Usage:
  python seo/live_verify.py [slug] [--wait 95]

`slug` is the blog slug, e.g. "dehydrate-apples-time". If omitted, the target is
taken from seo/keyword-library.csv: the published row with the highest
publish_date, then the highest id.

Checks:
  [1] clean URL 200 and the article's <h1> text is present
  [2] the same path with .html still 308-redirects and follows to the clean URL
  [3] /blog/ lists the new card and the "N Guides" count matches the count on disk
  [4] /sitemap.xml contains the new clean URL and zero ".html" occurrences
  [5] every local page linking to the new article returns 200 with the link intact

Exit code 0 = PASS, 1 = FAIL.
"""
import csv
import html as htmllib
import os
import re
import ssl
import sys
import time
import urllib.error
import urllib.request

BASE = "https://homesteadcalc.com"
CTX = ssl.create_default_context()
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(ROOT, "seo", "keyword-library.csv")

SKIP_DIRS = {".git", ".workbuddy", "node_modules", "seo"}


def fetch(path, follow=True, timeout=25):
    url = BASE + path
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (verify-bot)"})
    opener = urllib.request.build_opener(
        urllib.request.HTTPRedirectHandler() if follow else urllib.request.HTTPErrorProcessor()
    )
    try:
        with opener.open(req, timeout=timeout) as r:
            return r.status, r.geturl(), r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.geturl(), e.read()
    except Exception as e:
        return None, str(e), b""


def strip_tags(s):
    return re.sub(r"\s+", " ", htmllib.unescape(re.sub(r"<[^>]+>", " ", s))).strip()


def resolve_target(slug):
    """Return (slug, local_path, clean_url, expected_text)."""
    rows = list(csv.DictReader(open(CSV_PATH, encoding="utf-8-sig", newline="")))
    if slug:
        matches = [r for r in rows if r["slug"].strip().endswith("/%s.html" % slug)]
        if not matches:
            sys.exit("slug %r not found in keyword-library.csv" % slug)
        row = matches[0]
    else:
        published = [r for r in rows if r["status"].strip() == "published"]
        if not published:
            sys.exit("no published rows in keyword-library.csv")
        row = max(published, key=lambda r: (r["publish_date"].strip(), int(r["id"])))
        slug = os.path.basename(row["slug"].strip())[:-5]

    rel = row["slug"].strip()
    local = os.path.join(ROOT, rel.replace("/", os.sep))
    clean = "/" + rel[:-5]  # blog/foo.html -> /blog/foo

    if os.path.exists(local):
        page = open(local, encoding="utf-8").read()
        m = re.search(r"<h1[^>]*>(.*?)</h1>", page, re.S)
        expected = strip_tags(m.group(1)) if m else row["suggested_title"].strip()
    else:
        expected = row["suggested_title"].strip()
    return slug, local, clean, expected


def local_linkers(clean_url):
    """Every local html file that links to the new article (excluding the article)."""
    hits = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if not fn.endswith(".html"):
                continue
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, ROOT).replace(os.sep, "/")
            if rel == clean_url.lstrip("/") + ".html":
                continue
            try:
                if 'href="%s"' % clean_url in open(full, encoding="utf-8").read():
                    if fn == "index.html":
                        d = os.path.dirname(rel)
                        hits.append("/" if d == "." else "/" + d + "/")
                    else:
                        hits.append("/" + rel[:-5])
            except OSError:
                pass
    return sorted(set(hits))


def main():
    args = [a for a in sys.argv[1:]]
    wait = 95
    slug = None
    i = 0
    while i < len(args):
        if args[i] == "--wait":
            wait = int(args[i + 1]); i += 2
        elif args[i] == "--no-wait":
            wait = 0; i += 1
        else:
            slug = args[i]; i += 1

    slug, local, clean, expected = resolve_target(slug)
    print("target slug   : %s" % slug)
    print("clean URL     : %s" % clean)
    print("expected text : %s" % expected[:80])

    if wait:
        print("waiting %ds for Cloudflare Pages deploy ..." % wait, flush=True)
        time.sleep(wait)

    ok = True

    # 1) clean URL
    st, final, body = fetch(clean)
    text = body.decode("utf-8", "replace")
    hit = expected in htmllib.unescape(text)
    print("[1] %-38s status=%s final=%s bytes=%d h1_hit=%s" % (clean, st, final, len(body), hit))
    ok &= (st == 200 and final.rstrip("/") == BASE + clean and hit)

    # 2) .html must 308 -> clean
    st2, final2, body2 = fetch(clean + ".html")
    print("[2] %-38s status=%s final=%s bytes=%d" % (clean + ".html", st2, final2, len(body2)))
    ok &= (st2 == 200 and final2.rstrip("/") == BASE + clean)

    # 3) blog index card + guide count
    st3, _, body3 = fetch("/blog/")
    t3 = body3.decode("utf-8", "replace")
    card = 'href="%s"' % clean in t3
    n_guides = sum(
        1 for fn in os.listdir(os.path.join(ROOT, "blog"))
        if fn.endswith(".html") and fn != "index.html"
    )
    count_ok = ("%d Guides" % n_guides) in t3
    print("[3] %-38s status=%s bytes=%d new_card=%s count(%d)=%s"
          % ("/blog/", st3, len(body3), card, n_guides, count_ok))
    ok &= (st3 == 200 and card and count_ok)

    # 4) sitemap
    st4, _, body4 = fetch("/sitemap.xml")
    sm = body4.decode("utf-8", "replace")
    inmap = "%s%s<" % (BASE, clean) in sm
    htmlhits = sm.count(".html")
    print("[4] %-38s status=%s bytes=%d new_url=%s .html_hits=%d"
          % ("/sitemap.xml", st4, len(body4), inmap, htmlhits))
    ok &= (st4 == 200 and inmap and htmlhits == 0)

    # 5) reverse links
    linkers = local_linkers(clean)
    if not linkers:
        print("[5] no local pages link to %s -- FAIL" % clean)
        ok = False
    for p in linkers:
        st5, _, b5 = fetch(p)
        has = 'href="%s"' % clean in b5.decode("utf-8", "replace")
        print("[5] %-38s status=%s reverse_link=%s" % (p, st5, has))
        ok &= (st5 == 200 and has)

    print()
    print("LIVE VERIFICATION:", "PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
