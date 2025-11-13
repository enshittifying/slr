#!/usr/bin/env python3
"""
Offline scrapers for OLRC Tables I, II, IV, V, and VI from saved HTML.

Inputs (any subset present in cwd):
 - usctable1_*.html  (Table I — Revised Titles)
 - usctable2_*.html  (Table II — Revised Statutes 1878)
 - usctable4_*.html  (Table IV — Executive Orders)
 - usctable5_*.html  (Table V — Proclamations)
 - usctable6_*.html  (Table VI — Reorganization Plans)

Outputs: JSON per table under --outdir, optionally CSV and SQLite.

No third-party dependencies.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sqlite3
from glob import glob
from html import unescape
from typing import Any, Dict, List, Optional


def _read(path: str) -> str:
    with open(path, "rb") as f:
        return f.read().decode("utf-8", errors="replace")


def write_json(data: Any, path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def parse_table1(path: str) -> Dict[str, Any]:
    html = _read(path)
    records: List[Dict[str, str]] = []
    current_title: Optional[str] = None

    # Detect header rows to maintain context like "Title X"
    for m in re.finditer(r"<tr><th class=\"t1formersection\">(.*?)</th><th class=\"t1newsection\">(.*?)</th></tr>", html, flags=re.S):
        former_hdr = unescape(re.sub(r"<.*?>", "", m.group(1))).strip()
        # Example: "Title 1 Former Sections" -> Title 1
        mt = re.search(r"Title\s+([^\s]+)", former_hdr)
        current_title = mt.group(1) if mt else None

    # Row pairs
    for m in re.finditer(r"<tr><td class=\"t1formersection\">(.*?)</td><td class=\"t1newsection\">(.*?)</td></tr>", html, flags=re.S):
        former = unescape(re.sub(r"<.*?>", "", m.group(1))).strip()
        new = unescape(re.sub(r"<.*?>", "", m.group(2))).strip()
        records.append({
            "former_title": current_title,
            "former_section": former,
            "new_section_text": new,
        })

    return {"source_file": os.path.basename(path), "table": "I", "records": records}


def parse_table2(path: str) -> Dict[str, Any]:
    html = _read(path)
    # Locate the main data table block
    m = re.search(r"<!-- field-start:usctable2-tabledata -->(.*)<!-- field-end:usctable2-tabledata -->", html, flags=re.S)
    block = m.group(1) if m else html
    records: List[Dict[str, str]] = []
    # Rows are generic <tr><td>R.S.</td><td>Title</td><td>Section</td><td>Status</td></tr>
    for m in re.finditer(r"<tr><td>(.*?)</td><td>(.*?)</td><td>(.*?)</td><td>(.*?)</td></tr>", block, flags=re.S):
        rs = unescape(re.sub(r"<.*?>", "", m.group(1))).strip()
        title = unescape(re.sub(r"<.*?>", "", m.group(2))).strip()
        section = unescape(re.sub(r"<.*?>", "", m.group(3))).strip()
        status = unescape(re.sub(r"<.*?>", "", m.group(4))).strip()
        # Skip header-like empty lines
        if rs == "" and title == "Title":
            continue
        if rs == "R.S. Sec":
            continue
        records.append({
            "rs_section": rs,
            "usc_title": title,
            "usc_section": section,
            "status": status,
        })
    return {"source_file": os.path.basename(path), "table": "II", "records": records}


def parse_table4(path: str) -> Dict[str, Any]:
    html = _read(path)
    records: List[Dict[str, str]] = []
    current_year: Optional[str] = None
    # Identify year headers
    for part in re.split(r"(<tr><th colspan=\"6\" class=\"year\">.*?</th></tr>)", html):
        ym = re.match(r"<tr><th colspan=\"6\" class=\"year\">(.*?)</th></tr>", part)
        if ym:
            current_year = unescape(ym.group(1)).strip()
            continue
        # Rows
        for m in re.finditer(r"<tr class=\"usctable4row\"><td>(.*?)</td><td>(.*?)</td><td>(.*?)</td><td>(.*?)</td><td>(.*?)</td><td>(.*?)</td></tr>", part, flags=re.S):
            month = unescape(re.sub(r"<.*?>", "", m.group(1))).strip()
            day = unescape(re.sub(r"<.*?>", "", m.group(2))).strip()
            number = unescape(re.sub(r"<.*?>", "", m.group(3))).strip()
            title = unescape(re.sub(r"<.*?>", "", m.group(4))).strip()
            section = unescape(re.sub(r"<.*?>", "", m.group(5))).strip()
            status = unescape(re.sub(r"<.*?>", "", m.group(6))).strip()
            records.append({
                "year": current_year,
                "month": month,
                "day": day,
                "exec_order_no": number,
                "usc_title": title,
                "usc_section": section,
                "status": status,
            })
    return {"source_file": os.path.basename(path), "table": "IV", "records": records}


def parse_table5(path: str) -> Dict[str, Any]:
    html = _read(path)
    records: List[Dict[str, str]] = []
    current_year: Optional[str] = None
    for part in re.split(r"(<tr><th colspan=\"6\" class=\"year\">.*?</th></tr>)", html):
        ym = re.match(r"<tr><th colspan=\"6\" class=\"year\">(.*?)</th></tr>", part)
        if ym:
            current_year = unescape(ym.group(1)).strip()
            continue
        for m in re.finditer(r"<tr class=\"usctable5row\"><td>(.*?)</td><td>(.*?)</td><td>(.*?)</td><td>(.*?)</td><td>(.*?)</td><td>(.*?)</td></tr>", part, flags=re.S):
            month = unescape(re.sub(r"<.*?>", "", m.group(1))).strip()
            day = unescape(re.sub(r"<.*?>", "", m.group(2))).strip()
            number = unescape(re.sub(r"<.*?>", "", m.group(3))).strip()
            title = unescape(re.sub(r"<.*?>", "", m.group(4))).strip()
            section = unescape(re.sub(r"<.*?>", "", m.group(5))).strip()
            status = unescape(re.sub(r"<.*?>", "", m.group(6))).strip()
            records.append({
                "year": current_year,
                "month": month,
                "day": day,
                "proclamation_no": number,
                "usc_title": title,
                "usc_section": section,
                "status": status,
            })
    return {"source_file": os.path.basename(path), "table": "V", "records": records}


def parse_table6(path: str) -> Dict[str, Any]:
    html = _read(path)
    records: List[Dict[str, str]] = []
    current_header: Optional[str] = None
    for part in re.split(r"(<tr><th colspan=\"6\" class=\"year\">.*?</th></tr>)", html):
        ym = re.match(r"<tr><th colspan=\"6\" class=\"year\">(.*?)</th></tr>", part)
        if ym:
            current_header = unescape(ym.group(1)).strip()  # e.g., "1946 Plan No. 2"
            continue
        for m in re.finditer(r"<tr class=\"usctable6row\"><td>(.*?)</td><td>(.*?)</td><td>(.*?)</td><td>(.*?)</td><td>(.*?)</td><td>(.*?)</td></tr>", part, flags=re.S):
            coverage = unescape(re.sub(r"<.*?>", "", m.group(1))).strip()  # often "All"
            stat_vol = unescape(re.sub(r"<.*?>", "", m.group(2))).strip()
            stat_pg = unescape(re.sub(r"<.*?>", "", m.group(3))).strip()
            usc_title = unescape(re.sub(r"<.*?>", "", m.group(4))).strip()
            usc_section = unescape(re.sub(r"<.*?>", "", m.group(5))).strip()
            status = unescape(re.sub(r"<.*?>", "", m.group(6))).strip()
            records.append({
                "plan": current_header,
                "coverage": coverage,
                "stat_volume": stat_vol,
                "stat_page": stat_pg,
                "usc_title": usc_title,
                "usc_section": usc_section,
                "status": status,
            })
    return {"source_file": os.path.basename(path), "table": "VI", "records": records}


def write_csv(records: List[Dict[str, Any]], headers: List[str], out_path: str) -> None:
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=headers)
        w.writeheader()
        for r in records:
            w.writerow({k: r.get(k, "") for k in headers})


def write_table_sqlite(db: str, table: str, records: List[Dict[str, Any]], schema_sql: str, insert_sql: str, key_fields: Optional[List[str]] = None) -> None:
    if not records:
        return
    conn = sqlite3.connect(db)
    try:
        c = conn.cursor()
        c.execute(schema_sql)
        if key_fields:
            # delete existing rows with matching keys to avoid duplicates
            placeholders = " AND ".join([f"{k} = ?" for k in key_fields])
            for r in records:
                c.execute(f"DELETE FROM {table} WHERE {placeholders}", [r.get(k, "") for k in key_fields])
        for r in records:
            c.execute(insert_sql, [r.get(k, "") for k in re.findall(r":(\w+)", insert_sql)])
        conn.commit()
    finally:
        conn.close()


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Scrape OLRC Tables I, II, IV, V, VI from local HTML files.")
    ap.add_argument("--outdir", default="output_tables", help="Directory for JSON outputs.")
    ap.add_argument("--csv-outdir", default=None, help="If set, also write CSV files here.")
    ap.add_argument("--sqlite", default=None, help="If set, write results to this SQLite DB.")
    args = ap.parse_args(argv)

    # Discover available files
    files = {
        "I": sorted(glob("usctable1_*.html")),
        "II": sorted(glob("usctable2_*.html")),
        "IV": sorted(glob("usctable4_*.html")),
        "V": sorted(glob("usctable5_*.html")),
        "VI": sorted(glob("usctable6_*.html")),
    }

    # TABLE I
    for fp in files["I"]:
        t1 = parse_table1(fp)
        out_json = os.path.join(args.outdir, "usc_table1.json")
        write_json(t1, out_json)
        print(f"Wrote {out_json} ({len(t1['records'])} rows)")
        if args.csv_outdir:
            csvp = os.path.join(args.csv_outdir, "usc_table1.csv")
            write_csv(t1["records"], ["former_title", "former_section", "new_section_text"], csvp)
            print(f"CSV: {csvp}")
        if args.sqlite:
            write_table_sqlite(
                args.sqlite,
                table="t1_mappings",
                records=t1["records"],
                schema_sql=(
                    "CREATE TABLE IF NOT EXISTS t1_mappings (former_title TEXT, former_section TEXT, new_section_text TEXT)"
                ),
                insert_sql=(
                    "INSERT INTO t1_mappings (former_title, former_section, new_section_text) VALUES (:former_title, :former_section, :new_section_text)"
                ),
                key_fields=["former_title", "former_section", "new_section_text"],
            )
            print(f"SQLite updated: {args.sqlite} (t1_mappings)")

    # TABLE II
    for fp in files["II"]:
        t2 = parse_table2(fp)
        out_json = os.path.join(args.outdir, "usc_table2.json")
        write_json(t2, out_json)
        print(f"Wrote {out_json} ({len(t2['records'])} rows)")
        if args.csv_outdir:
            csvp = os.path.join(args.csv_outdir, "usc_table2.csv")
            write_csv(t2["records"], ["rs_section", "usc_title", "usc_section", "status"], csvp)
            print(f"CSV: {csvp}")
        if args.sqlite:
            write_table_sqlite(
                args.sqlite,
                table="t2_revstat",
                records=t2["records"],
                schema_sql=(
                    "CREATE TABLE IF NOT EXISTS t2_revstat (rs_section TEXT, usc_title TEXT, usc_section TEXT, status TEXT)"
                ),
                insert_sql=(
                    "INSERT INTO t2_revstat (rs_section, usc_title, usc_section, status) VALUES (:rs_section, :usc_title, :usc_section, :status)"
                ),
                key_fields=["rs_section", "usc_title", "usc_section", "status"],
            )
            print(f"SQLite updated: {args.sqlite} (t2_revstat)")

    # TABLE IV
    for fp in files["IV"]:
        t4 = parse_table4(fp)
        out_json = os.path.join(args.outdir, "usc_table4.json")
        write_json(t4, out_json)
        print(f"Wrote {out_json} ({len(t4['records'])} rows)")
        if args.csv_outdir:
            csvp = os.path.join(args.csv_outdir, "usc_table4.csv")
            write_csv(t4["records"], ["year", "month", "day", "exec_order_no", "usc_title", "usc_section", "status"], csvp)
            print(f"CSV: {csvp}")
        if args.sqlite:
            write_table_sqlite(
                args.sqlite,
                table="t4_exec_orders",
                records=t4["records"],
                schema_sql=(
                    "CREATE TABLE IF NOT EXISTS t4_exec_orders (year TEXT, month TEXT, day TEXT, exec_order_no TEXT, usc_title TEXT, usc_section TEXT, status TEXT)"
                ),
                insert_sql=(
                    "INSERT INTO t4_exec_orders (year, month, day, exec_order_no, usc_title, usc_section, status) VALUES (:year, :month, :day, :exec_order_no, :usc_title, :usc_section, :status)"
                ),
                key_fields=["year", "exec_order_no", "usc_title", "usc_section"],
            )
            print(f"SQLite updated: {args.sqlite} (t4_exec_orders)")

    # TABLE V
    for fp in files["V"]:
        t5 = parse_table5(fp)
        out_json = os.path.join(args.outdir, "usc_table5.json")
        write_json(t5, out_json)
        print(f"Wrote {out_json} ({len(t5['records'])} rows)")
        if args.csv_outdir:
            csvp = os.path.join(args.csv_outdir, "usc_table5.csv")
            write_csv(t5["records"], ["year", "month", "day", "proclamation_no", "usc_title", "usc_section", "status"], csvp)
            print(f"CSV: {csvp}")
        if args.sqlite:
            write_table_sqlite(
                args.sqlite,
                table="t5_proclamations",
                records=t5["records"],
                schema_sql=(
                    "CREATE TABLE IF NOT EXISTS t5_proclamations (year TEXT, month TEXT, day TEXT, proclamation_no TEXT, usc_title TEXT, usc_section TEXT, status TEXT)"
                ),
                insert_sql=(
                    "INSERT INTO t5_proclamations (year, month, day, proclamation_no, usc_title, usc_section, status) VALUES (:year, :month, :day, :proclamation_no, :usc_title, :usc_section, :status)"
                ),
                key_fields=["year", "proclamation_no", "usc_title", "usc_section"],
            )
            print(f"SQLite updated: {args.sqlite} (t5_proclamations)")

    # TABLE VI
    for fp in files["VI"]:
        t6 = parse_table6(fp)
        out_json = os.path.join(args.outdir, "usc_table6.json")
        write_json(t6, out_json)
        print(f"Wrote {out_json} ({len(t6['records'])} rows)")
        if args.csv_outdir:
            csvp = os.path.join(args.csv_outdir, "usc_table6.csv")
            write_csv(t6["records"], ["plan", "coverage", "stat_volume", "stat_page", "usc_title", "usc_section", "status"], csvp)
            print(f"CSV: {csvp}")
        if args.sqlite:
            write_table_sqlite(
                args.sqlite,
                table="t6_reorg_plans",
                records=t6["records"],
                schema_sql=(
                    "CREATE TABLE IF NOT EXISTS t6_reorg_plans (plan TEXT, coverage TEXT, stat_volume TEXT, stat_page TEXT, usc_title TEXT, usc_section TEXT, status TEXT)"
                ),
                insert_sql=(
                    "INSERT INTO t6_reorg_plans (plan, coverage, stat_volume, stat_page, usc_title, usc_section, status) VALUES (:plan, :coverage, :stat_volume, :stat_page, :usc_title, :usc_section, :status)"
                ),
                key_fields=["plan", "usc_title", "usc_section", "stat_volume", "stat_page"],
            )
            print(f"SQLite updated: {args.sqlite} (t6_reorg_plans)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

