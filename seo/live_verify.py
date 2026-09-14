#!/usr/bin/env python3
"""Post-deploy live verification for homesteadcalc.com (Cloudflare Pages clean URLs)."""
import time, ssl, urllib.request, urllib.error, sys

BASE = "https://homesteadcalc.com"
CTX = ssl.create_default_context()
WAIT = 95

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

def main():
    print(f"waiting {WAIT}s for Cloudflare Pages deploy ...", flush=True)
    time.sleep(WAIT)

    ok = True

    # 1) clean URL
    st, final, body = fetch("/blog/goats-per-acre")
    text = body.decode("utf-8", "replace")
    hit = "How Many Goats Per Acre? Stocking Rates by Forage" in text
    print(f"[1] /blog/goats-per-acre      status={st} final={final} bytes={len(body)} title_hit={hit}")
    ok &= (st == 200 and final.endswith("/blog/goats-per-acre") and hit)

    # 2) .html URL should 308 -> clean
    st2, final2, body2 = fetch("/blog/goats-per-acre.html")
    print(f"[2] /blog/goats-per-acre.html status={st2} final={final2} bytes={len(body2)}")
    ok &= (st2 == 200 and final2.endswith("/blog/goats-per-acre"))

    # 3) blog index carries the new card
    st3, final3, body3 = fetch("/blog/")
    t3 = body3.decode("utf-8", "replace")
    card = 'href="/blog/goats-per-acre"' in t3
    count31 = "31 Guides" in t3
    print(f"[3] /blog/                    status={st3} bytes={len(body3)} new_card={card} count31={count31}")
    ok &= (st3 == 200 and card and count31)

    # 4) sitemap
    st4, final4, body4 = fetch("/sitemap.xml")
    sm = body4.decode("utf-8", "replace")
    inmap = "https://homesteadcalc.com/blog/goats-per-acre<" in sm
    htmlhits = sm.count(".html")
    print(f"[4] /sitemap.xml              status={st4} bytes={len(body4)} new_url={inmap} .html_hits={htmlhits}")
    ok &= (st4 == 200 and inmap and htmlhits == 0)

    # 5) reverse link pages live
    for p in ["/calculators/land-requirement", "/calculators/goat-sheep-feed", "/blog/hay-per-goat-per-day"]:
        st5, f5, b5 = fetch(p)
        has = 'href="/blog/goats-per-acre"' in b5.decode("utf-8", "replace")
        print(f"[5] {p:<34} status={st5} reverse_link={has}")
        ok &= (st5 == 200 and has)

    print()
    print("LIVE VERIFICATION:", "PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
