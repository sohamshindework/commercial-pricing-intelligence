"""Download UCI Online Retail II, verify checksums and write the landing Parquet file.

Usage:
    python scripts/download.py            # download (if needed), verify, convert
    python scripts/download.py --force    # re-download even if the zip exists
"""

from __future__ import annotations

import argparse

from commercial_intelligence.common.config import load_settings, repo_path
from commercial_intelligence.ingestion.download import (
    download_file,
    extract_member,
    verify_checksum,
)
from commercial_intelligence.ingestion.landing import excel_to_landing


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="re-download the archive")
    args = parser.parse_args()

    settings = load_settings()
    ds, paths = settings["dataset"], settings["paths"]
    raw_dir = repo_path(paths["raw_dir"])
    raw_dir.mkdir(parents=True, exist_ok=True)

    zip_path = raw_dir / "online_retail_ii.zip"
    if args.force or not zip_path.exists():
        download_file(ds["url"], zip_path)
    verify_checksum(zip_path, ds["zip_sha256"])

    xlsx_path = extract_member(zip_path, ds["xlsx_name"], raw_dir)
    verify_checksum(xlsx_path, ds["xlsx_sha256"])

    excel_to_landing(xlsx_path, repo_path(paths["landing_parquet"]))


if __name__ == "__main__":
    main()
