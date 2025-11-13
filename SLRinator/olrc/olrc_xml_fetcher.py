#!/usr/bin/env python3
"""
Scaffold to fetch OLRC Table III XML zip archives and extract them locally.

Note: Requires network access. Defaults are based on OLRC links observed in
saved HTML (table3-xml-bulk.zip and table3-xml-acts.zip under /table3/).

This script does not parse the XML; it only downloads and extracts for use by
other tools. Parsing can be added once sample XML is available locally.
"""

from __future__ import annotations

import argparse
import os
import sys
import urllib.request
import zipfile

DEFAULT_BASE = "https://uscode.house.gov/table3/"
DEFAULT_FILES = [
    "table3-xml-bulk.zip",
    "table3-xml-acts.zip",
]


def download(url: str, dest: str) -> str:
    os.makedirs(dest, exist_ok=True)
    local = os.path.join(dest, os.path.basename(url))
    print(f"Downloading {url} -> {local} ...")
    urllib.request.urlretrieve(url, local)  # nosec - trusted OLRC host
    return local


def extract(zip_path: str, dest: str) -> None:
    print(f"Extracting {zip_path} -> {dest} ...")
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(dest)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Fetch and extract OLRC Table III XML archives.")
    ap.add_argument("--base", default=DEFAULT_BASE, help="Base URL for OLRC Table III files.")
    ap.add_argument("--files", nargs="*", default=DEFAULT_FILES, help="Zip filenames to fetch from base URL.")
    ap.add_argument("--download-dir", default="olrc_xml_zips", help="Directory to store downloaded zips.")
    ap.add_argument("--extract-dir", default="olrc_xml", help="Directory to extract XML contents.")
    args = ap.parse_args(argv)

    try:
        for name in args.files:
            url = args.base.rstrip("/") + "/" + name
            z = download(url, args.download_dir)
            extract(z, args.extract_dir)
        print("Done.")
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

