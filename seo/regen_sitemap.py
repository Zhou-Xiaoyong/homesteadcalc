#!/usr/bin/env python3
"""
Full sitemap regeneration + validation for homesteadcalc.com (Cloudflare Pages, clean URLs).

Scans every .html on disk, excludes 404 / noindex / drafts / verification files,
emits clean (extensionless) URLs, preserves existing lastmod for untouched pages,
then hard-validates the result.

Usage:  python seo/regen_sitemap.py [--changed path1 path2 ...] [--date YYYY-MM-DD]
Exit 0 = all checks pass, 1 = failure.
"""
import os, re, sys, argparse, xml.etree.ElementTree as ET
from datetime import date

SITE = "https://homesteadcalc.com"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITEMAP = os.path.join(ROOT, "sitemap.xml")

EXCLUDE_DIRS = {".git", ".workbuddy", "seo", "node_modules"}
EXCLUDE_FILES = {"404.html"}
EXCLUDE_PATTERNS = [
    re.compile(r"^baidu_verify_", re.I),
    re.compile(r"^google[0-9a-f]{16}\.html$", re.I),
    re.compile(r"(template|draft|test|sample|backup|copy)", re.I),
]

PRIORITY = {"root": "1.0", "section": "0.9", "calculators": "0.8",
            "printables": "0.7", "blog": "0.7", "legal": "0.3", "page": "0.5"}
CHANGEFREQ = {"root": "weekly", "section": "weekly", "calculators": "monthly",
              "printables": "monthly", "blog": "monthly", "legal": "yearly", "page": "monthly"}
LEGAL = {"privacy-policy", "terms"}


def clean_url(rel):
    """foo.html -> /foo ; dir/index.html -> /dir/ ; index.html -> /"""
    rel = rel.replace(os.sep, "/")
    if rel == "index.html":
        return SITE + "/"
    if rel.endswith("/index.html"):
        return SITE + "/" + rel[: -len("index.html")]
    return SITE + "/" + rel[: -len(".html")]


def classify(rel):
    rel = rel.replace(os.sep, "/")
    if rel == "index.html":
        return "root"
    if rel.endswith("/index.html"):
        return "section"
    top = rel.split("/")[0]
    stem = os.path.splitext(os.path.basename(rel))[0]
    if stem in LEGAL:
        return "legal"
    if top in ("calculators", "printables", "blog"):
        return top
    return "page"


def discover():
    pages, skipped = [], []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS and not d.startswith(".")]
        for fn in filenames:
            if not fn.endswith(".html"):
                continue
            rel = os.path.relpath(os.path.join(dirpath, fn), ROOT)
            if fn in EXCLUDE_FILES:
                skipped.append((rel, "excluded filename")); continue
            if any(p.search(fn) for p in EXCLUDE_PATTERNS):
                skipped.append((rel, "excluded pattern")); continue
            html = open(os.path.join(dirpath, fn), encoding="utf-8", errors="replace").read()
            if re.search(r'<meta[^>]+name=["\']robots["\'][^>]*content=["\'][^"\']*noindex', html, re.I):
                skipped.append((rel, "noindex")); continue
            pages.append(rel.replace(os.sep, "/"))
    return sorted(pages), skipped


def existing_entries():
    """Preserve hand-tuned lastmod / changefreq / priority from the current sitemap."""
    if not os.path.exists(SITEMAP):
        return {}
    ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    tree = ET.parse(SITEMAP)
    out = {}
    for u in tree.getroot().findall("s:url", ns):
        loc = u.findtext("s:loc", default="", namespaces=ns).strip()
        if loc:
            out[loc] = {
                "lastmod": u.findtext("s:lastmod", default="", namespaces=ns).strip(),
                "changefreq": u.findtext("s:changefreq", default="", namespaces=ns).strip(),
                "priority": u.findtext("s:priority", default="", namespaces=ns).strip(),
            }
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--changed", nargs="*", default=[])
    ap.add_argument("--date", default=date.today().isoformat())
    args = ap.parse_args()

    today = args.date
    changed = {c.replace("\\", "/").lstrip("./") for c in args.changed}
    pages, skipped = discover()
    old = existing_entries()

    entries, new_pages = [], []
    for rel in pages:
        loc = clean_url(rel)
        kind = classify(rel)
        prev = old.get(loc)
        if prev is None:
            new_pages.append(rel)
        lm = today if (rel in changed or prev is None) else (prev["lastmod"] or today)
        cf = (prev or {}).get("changefreq") or CHANGEFREQ[kind]
        pr = (prev or {}).get("priority") or PRIORITY[kind]
        entries.append((loc, lm, cf, pr, rel))

    # stable ordering: keep previous sitemap order where possible, append new at end of section
    order = {loc: i for i, loc in enumerate(old)}
    entries.sort(key=lambda e: (order.get(e[0], 10_000 + pages.index(e[4])),))

    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc, lm, cf, pr, _ in entries:
        lines += ["  <url>", f"    <loc>{loc}</loc>", f"    <lastmod>{lm}</lastmod>",
                  f"    <changefreq>{cf}</changefreq>", f"    <priority>{pr}</priority>", "  </url>"]
    lines.append("</urlset>")
    xml = "\n".join(lines) + "\n"
    open(SITEMAP, "w", encoding="utf-8", newline="\n").write(xml)

    # ---------------- validation ----------------
    fails = []
    try:
        root = ET.fromstring(xml)
    except Exception as e:
        print(f"FAIL parse: {e}"); sys.exit(1)

    ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    locs = [u.findtext("s:loc", namespaces=ns) for u in root.findall("s:url", ns)]

    if len(locs) != len(set(locs)):
        dupes = {l for l in locs if locs.count(l) > 1}
        fails.append(f"duplicate <loc>: {dupes}")
    if xml.count(".html") != 0:
        fails.append(f".html found in sitemap ({xml.count('.html')} hits)")
    if len(locs) != len(pages):
        fails.append(f"URL count {len(locs)} != indexable pages {len(pages)}")

    # every page's canonical + og:url must exist and equal its own clean URL
    for rel in pages:
        want = clean_url(rel)
        html = open(os.path.join(ROOT, rel), encoding="utf-8", errors="replace").read()
        can = re.search(r'<link[^>]+rel=["\']canonical["\'][^>]+href=["\']([^"\']+)["\']', html, re.I)
        og = re.search(r'<meta[^>]+property=["\']og:url["\'][^>]+content=["\']([^"\']+)["\']', html, re.I)
        if not can:
            fails.append(f"{rel}: MISSING canonical")
        elif can.group(1).rstrip("/") != want.rstrip("/"):
            fails.append(f"{rel}: canonical {can.group(1)} != {want}")
        if not og:
            fails.append(f"{rel}: MISSING og:url")
        elif og.group(1).rstrip("/") != want.rstrip("/"):
            fails.append(f"{rel}: og:url {og.group(1)} != {want}")

    print(f"pages discovered : {len(pages)}")
    print(f"pages skipped    : {len(skipped)}  {[s[0] for s in skipped]}")
    print(f"urls written     : {len(locs)}")
    print(f"lastmod={today}  : {sum(1 for e in entries if e[1] == today)}")
    print(f"new pages        : {new_pages}")
    if fails:
        print("\n--- VALIDATION FAILURES ---")
        for f in fails:
            print("  X " + f)
        sys.exit(1)
    print("\nAll checks PASSED: xml valid | no dupes | zero .html | count matches | canonical+og:url consistent")


if __name__ == "__main__":
    main()
