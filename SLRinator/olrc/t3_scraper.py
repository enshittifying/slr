#!/usr/bin/env python3
"""
Offline scraper for OLRC United States Code Table III (T3).

Parses locally saved OLRC HTML pages (years and acts) to extract
codification mappings from session laws to the U.S. Code.

Inputs: files like
 - table3years_*.html (optional, for reference)
 - year{YYYY}_*.html (year index pages)
 - {ACT_BASE}_*.html where ACT_BASE looks like 113_146 or 1790_9

Outputs:
 - output/t3_year_{YYYY}.json: list of acts with rows

No third-party dependencies are required.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, asdict
import csv
import sqlite3
from glob import glob
from html import unescape
from typing import List, Optional, Dict, Any


@dataclass
class T3Row:
    act_section: str
    stat_page: str
    us_title: str
    us_section: str
    status: str


@dataclass
class T3Act:
    act_id: str           # e.g., "113–146" or "1790:9"
    act_base: str         # e.g., "113_146" or "1790_9"
    congress: str         # e.g., "113th Cong."
    stat_volume: str      # e.g., "128 Stat."
    date_text: str        # e.g., "Aug. 7, 2014"
    year: Optional[int]   # e.g., 2014
    rows: List[T3Row]
    source_file: str


YEAR_FILENAME_RE = re.compile(r"^year(\d{4})_.*\.html$")
ACT_LINK_RE = re.compile(r"<span class=\"yearmasterfilelink\d+\"><a href=\"([^\"]+)\">([^<]+)</a></span>")


def _read(path: str) -> str:
    with open(path, "rb") as f:
        data = f.read()
    # Attempt to decode as UTF-8; OLRC pages are UTF-8.
    try:
        return data.decode("utf-8", errors="replace")
    except Exception:
        return data.decode(errors="replace")


def _text_between(tag: str, cls: str, html: str) -> Optional[str]:
    # Extract text content before the first nested tag. Useful when visible text
    # precedes a link, e.g., <span class="act">113–146<a ...>
    pattern = rf"<{tag} class=\"{re.escape(cls)}\">(.*?)</{tag}>"
    m = re.search(pattern, html, flags=re.S)
    if not m:
        return None
    inner = m.group(1)
    text = re.split(r"<", inner, maxsplit=1)[0]
    return unescape(text).strip()


def _text_content(tag: str, cls: str, html: str) -> Optional[str]:
    # Extract full text content (tags stripped) from a tag with class.
    pattern = rf"<{tag} class=\"{re.escape(cls)}\">(.*?)</{tag}>"
    m = re.search(pattern, html, flags=re.S)
    if not m:
        return None
    inner = m.group(1)
    text = re.sub(r"<.*?>", "", inner)
    return unescape(" ".join(text.split()))


def _extract_year_from_context(html: str) -> Optional[int]:
    # Within <span class="textdate">Aug. 7, <a ...>2014</a> ...
    m = re.search(r"<span class=\"textdate\">(.*?)</span>", html, flags=re.S)
    if not m:
        return None
    seg = m.group(1)
    y = re.search(r">(\d{4})<", seg)
    return int(y.group(1)) if y else None


def parse_act_file(path: str) -> Optional[T3Act]:
    html = _read(path)

    # Identify act_base from filename prefix (e.g., 113_146)
    basename = os.path.basename(path)
    act_base = os.path.splitext(basename)[0]
    # Drop trailing timestamp suffix after the second underscore, if any
    # Examples: 113_146_20250926_173758 -> 113_146
    m = re.match(r"^(\d+_\d+)(?:_.*)?$", act_base)
    if not m:
        m2 = re.match(r"^(\d{4}_\d+)(?:_.*)?$", act_base)
        act_base = m2.group(1) if m2 else act_base
    else:
        act_base = m.group(1)

    congress = _text_content("span", "congress", html) or ""
    congress = congress.replace("↑", "").strip()
    stat_volume = _text_content("span", "statutesatlargevolume", html) or ""
    # stat_volume span includes nested <a>; keep visible text before link arrow
    stat_volume = re.sub(r"\s*↑\s*\Z", "", stat_volume).strip()
    date_text = _text_content("span", "textdate", html) or ""
    date_text = date_text.replace("↑", "").strip()
    act_id = _text_between("span", "act", html) or ""
    year = _extract_year_from_context(html)

    # Rows: iterate over tr with classes table3row_odd/even
    rows: List[T3Row] = []
    for m in re.finditer(r"<tr class=\"table3row_(?:odd|even)\">(.*?)</tr>", html, flags=re.S):
        row_html = m.group(1)

        def cell(cls: str) -> str:
            # Extract text from <td class="cls"> ... possibly with nested <a>
            cm = re.search(rf"<td class=\"{re.escape(cls)}\">(.*?)</td>", row_html, flags=re.S)
            if not cm:
                return ""
            inner = cm.group(1)
            # If there is an anchor, prefer its text
            am = re.search(r">([^<>]+)</a>\s*$", inner.strip(), flags=re.S)
            if am:
                return unescape(am.group(1)).strip()
            # Otherwise, plain text
            text = re.sub(r"<.*?>", "", inner)
            return unescape(text).strip()

        act_section = cell("actsection")
        stat_page = cell("statutesatlargepage")
        us_title = cell("unitedstatescodetitle")
        us_section = cell("unitedstatescodesection")
        status = cell("unitedstatescodestatus")

        # Skip empty spacer rows, if any
        if not (act_section or stat_page or us_title or us_section or status):
            continue
        rows.append(T3Row(
            act_section=act_section,
            stat_page=stat_page,
            us_title=us_title,
            us_section=us_section,
            status=status,
        ))

    if not act_id and not rows:
        return None

    return T3Act(
        act_id=act_id,
        act_base=act_base,
        congress=congress,
        stat_volume=stat_volume,
        date_text=date_text,
        year=year,
        rows=rows,
        source_file=basename,
    )


def parse_year_file(path: str) -> Dict[str, Any]:
    html = _read(path)
    acts: List[Dict[str, str]] = []
    for link, text in ACT_LINK_RE.findall(html):
        # link like '113_146.htm' -> base '113_146'
        base = os.path.splitext(os.path.basename(link))[0]
        acts.append({"act_base": base, "label": unescape(text)})

    # Also collect nav context for year
    ym = re.search(YEAR_FILENAME_RE, os.path.basename(path))
    year: Optional[int] = int(ym.group(1)) if ym else None
    return {"year": year, "acts": acts, "source_file": os.path.basename(path)}


def find_local_act_file(act_base: str) -> Optional[str]:
    # Prefer exact prefix matches: e.g., 113_146_*.html
    candidates = sorted(glob(f"{act_base}_*.html"))
    if candidates:
        return candidates[0]
    # Fallback to exact name if provided
    exact = f"{act_base}.html"
    return exact if os.path.exists(exact) else None


def scrape_year(year_file: str) -> Dict[str, Any]:
    yinfo = parse_year_file(year_file)
    year = yinfo.get("year")
    acts_info: List[Dict[str, Any]] = []
    for entry in yinfo["acts"]:
        base = entry["act_base"]
        local = find_local_act_file(base)
        if not local:
            acts_info.append({
                "act_base": base,
                "label": entry.get("label"),
                "error": "local act file not found"
            })
            continue
        act = parse_act_file(local)
        if not act:
            acts_info.append({
                "act_base": base,
                "label": entry.get("label"),
                "error": "failed to parse act file",
                "source_file": os.path.basename(local),
            })
            continue
        act_d = asdict(act)
        acts_info.append(act_d)

    return {
        "year": year,
        "year_source_file": os.path.basename(year_file),
        "acts": acts_info,
    }


def write_json(obj: Any, out_path: str) -> None:
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def write_t3_csv(year_obj: Dict[str, Any], outdir: str) -> str:
    os.makedirs(outdir, exist_ok=True)
    year = year_obj.get("year") or year_obj.get("year_source_file", "unknown")
    out_path = os.path.join(outdir, f"t3_year_{year}.csv")
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "act_id", "act_base", "congress", "stat_volume", "date_text", "year",
            "act_section", "stat_page", "us_title", "us_section", "status", "source_file"
        ])
        for act in year_obj.get("acts", []):
            if "rows" not in act:
                # summarize missing acts with a single row noting the error
                w.writerow([
                    act.get("act_id", ""), act.get("act_base", ""), "", "", "",
                    year_obj.get("year", ""), "", "", "", "", act.get("error", ""),
                    act.get("source_file", "")
                ])
                continue
            for row in act.get("rows", []):
                w.writerow([
                    act.get("act_id", ""), act.get("act_base", ""), act.get("congress", ""),
                    act.get("stat_volume", ""), act.get("date_text", ""), act.get("year", ""),
                    row.get("act_section", ""), row.get("stat_page", ""), row.get("us_title", ""),
                    row.get("us_section", ""), row.get("status", ""), act.get("source_file", "")
                ])
    return out_path


def write_t3_sqlite(year_obj: Dict[str, Any], db_path: str) -> None:
    acts = [a for a in year_obj.get("acts", []) if "rows" in a]
    if not acts:
        return
    conn = sqlite3.connect(db_path)
    try:
        c = conn.cursor()
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS t3_acts (
                act_base TEXT PRIMARY KEY,
                act_id TEXT,
                congress TEXT,
                stat_volume TEXT,
                date_text TEXT,
                year INTEGER,
                source_file TEXT
            )
            """
        )
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS t3_rows (
                act_base TEXT,
                act_section TEXT,
                stat_page TEXT,
                us_title TEXT,
                us_section TEXT,
                status TEXT,
                FOREIGN KEY(act_base) REFERENCES t3_acts(act_base)
            )
            """
        )
        # Remove prior rows for acts being inserted to avoid duplicates on rerun
        act_bases = [a.get("act_base", "") for a in acts if a.get("act_base")]
        if act_bases:
            qmarks = ",".join(["?"] * len(act_bases))
            c.execute(f"DELETE FROM t3_rows WHERE act_base IN ({qmarks})", act_bases)
            c.execute(f"DELETE FROM t3_acts WHERE act_base IN ({qmarks})", act_bases)

        # Insert
        for a in acts:
            c.execute(
                "INSERT INTO t3_acts (act_base, act_id, congress, stat_volume, date_text, year, source_file) VALUES (?,?,?,?,?,?,?)",
                (
                    a.get("act_base", ""), a.get("act_id", ""), a.get("congress", ""),
                    a.get("stat_volume", ""), a.get("date_text", ""), a.get("year"), a.get("source_file", "")
                ),
            )
            for r in a.get("rows", []):
                c.execute(
                    "INSERT INTO t3_rows (act_base, act_section, stat_page, us_title, us_section, status) VALUES (?,?,?,?,?,?)",
                    (
                        a.get("act_base", ""), r.get("act_section", ""), r.get("stat_page", ""),
                        r.get("us_title", ""), r.get("us_section", ""), r.get("status", "")
                    ),
                )
        conn.commit()
    finally:
        conn.close()


def discover_year_files() -> List[str]:
    return sorted(glob("year*_*.html"))


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(description="Scrape OLRC Table III from local HTML files.")
    p.add_argument("--year-file", action="append", default=[], help="Specific year HTML file(s) to parse.")
    p.add_argument("--act-file", action="append", default=[], help="Specific act HTML file(s) to parse (debug).")
    p.add_argument("--outdir", default="output", help="Directory for JSON outputs.")
    p.add_argument("--csv-outdir", default=None, help="If set, also write per-year CSV to this directory.")
    p.add_argument("--sqlite", default=None, help="If set, write/append results to this SQLite database file.")
    args = p.parse_args(argv)

    # Debug mode: parse act files only
    if args.act_file:
        results = []
        for path in args.act_file:
            act = parse_act_file(path)
            results.append(asdict(act) if act else {"source_file": os.path.basename(path), "error": "failed to parse"})
        out_path = os.path.join(args.outdir, "t3_acts_debug.json")
        write_json(results, out_path)
        print(f"Wrote {out_path} ({len(results)} items)")
        return 0

    year_files = args.year_file or discover_year_files()
    if not year_files:
        print("No year*_*.html files found.", file=sys.stderr)
        return 1

    for yf in year_files:
        yobj = scrape_year(yf)
        year = yobj.get("year") or os.path.basename(yf)
        out_path = os.path.join(args.outdir, f"t3_year_{year}.json")
        write_json(yobj, out_path)
        msg = [f"Wrote {out_path} with {len(yobj['acts'])} acts"]
        if args.csv_outdir:
            csv_path = write_t3_csv(yobj, args.csv_outdir)
            msg.append(f"CSV: {csv_path}")
        if args.sqlite:
            write_t3_sqlite(yobj, args.sqlite)
            msg.append(f"SQLite: {args.sqlite}")
        print(" | ".join(msg))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
