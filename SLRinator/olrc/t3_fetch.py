#!/usr/bin/env python3
"""
Crawler to fetch OLRC Table III (Statutes at Large → U.S. Code) pages.

Start URL: https://uscode.house.gov/table3/table3years.htm
For each year: https://uscode.house.gov/table3/yearYYYY.htm
For each act link on a year page:
 - Old format: https://uscode.house.gov/table3/1789_1.htm (shown in year pages as 1789:1)
 - Modern format: https://uscode.house.gov/table3/88_439.htm (shown as 88–439, etc.)

Saves files with timestamped names compatible with t3_scraper.py.
No third-party dependencies.
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import sys
import time
from html import unescape
from typing import List, Tuple, Optional, Set

try:
    import urllib.request
    import urllib.error
except Exception as e:  # pragma: no cover
    print(f"Error importing urllib: {e}", file=sys.stderr)
    raise


BASE = "https://uscode.house.gov/table3/"
YEARS_PATH = "table3years.htm"


def ts() -> str:
    return dt.datetime.now().strftime("%Y%m%d_%H%M%S")


def fetch(url: str, retries: int = 3, delay: float = 0.5) -> bytes:
    last_err: Optional[Exception] = None
    for _ in range(retries):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "SLRinator-OLRC-Fetch/1.0 (+https://github.com/openai/)"
            })
            with urllib.request.urlopen(req, timeout=30) as resp:  # nosec - trusted host
                return resp.read()
        except Exception as e:
            last_err = e
            time.sleep(delay)
    raise last_err if last_err else RuntimeError("fetch failed")


def save_bytes(data: bytes, filename: str) -> str:
    with open(filename, "wb") as f:
        f.write(data)
    return filename


def parse_year_links(html: str) -> List[Tuple[int, str]]:
    # returns list of (year, href)
    out: List[Tuple[int, str]] = []
    for m in re.finditer(r"<a href=\"(year(\d{4})\.htm)\">\2</a>", html):
        href = m.group(1)
        year = int(m.group(2))
        out.append((year, href))
    return out


def parse_act_links(html: str) -> List[str]:
    # Finds links like 113_146.htm or 1790_9.htm inside year pages
    links: Set[str] = set()
    for m in re.finditer(r"<span class=\"yearmasterfilelink\d+\"><a href=\"([0-9]+_[0-9]+)\.htm\">", html):
        links.add(m.group(1) + ".htm")
    return sorted(links)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Fetch OLRC Table III pages (years and acts).")
    ap.add_argument("--base", default=BASE, help="Base URL for table3.")
    ap.add_argument("--years", nargs="*", type=int, help="Specific years to fetch (e.g., 2014 1946). Default: all years from years index.")
    ap.add_argument("--delay", type=float, default=0.4, help="Delay between requests (seconds).")
    ap.add_argument("--force", action="store_true", help="Overwrite existing files.")
    args = ap.parse_args(argv)

    base = args.base.rstrip("/") + "/"
    years_url = base + YEARS_PATH
    print(f"Fetching years index: {years_url}")
    years_html = fetch(years_url).decode("utf-8", errors="replace")
    years = parse_year_links(years_html)

    if args.years:
        years = [(y, f"year{y}.htm") for y in args.years]

    stamp = ts()
    # Save the years page for reference
    save_bytes(years_html.encode("utf-8"), f"table3years_{stamp}.html")

    for year, href in years:
        yurl = base + href
        print(f"Year {year}: {yurl}")
        yhtml_b = fetch(yurl)
        yhtml = yhtml_b.decode("utf-8", errors="replace")
        yfile = f"year{year}_{stamp}.html"
        if not os.path.exists(yfile) or args.force:
            save_bytes(yhtml_b, yfile)
        time.sleep(args.delay)

        acts = parse_act_links(yhtml)
        print(f"  Found {len(acts)} act pages")
        for a in acts:
            aurl = base + a
            abase = os.path.splitext(os.path.basename(a))[0]
            afile = f"{abase}_{stamp}.html"
            if os.path.exists(afile) and not args.force:
                continue
            try:
                ab = fetch(aurl)
                save_bytes(ab, afile)
            except Exception as e:
                print(f"    WARN: failed {aurl}: {e}")
            time.sleep(args.delay)

    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

