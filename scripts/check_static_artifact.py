"""Fail if the built portfolio artifact contains private or backend-only material."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

FORBIDDEN_SUFFIXES = {".csv", ".duckdb", ".parquet", ".xlsx", ".xls", ".zip", ".pem", ".key"}
FORBIDDEN_TEXT = (
    "/Users/",
    "data/warehouse",
    "online_retail_II.xlsx",
    "customer_key",
    "customer_id",
    "invoice_no",
    "source_row",
    "localhost:8000",
    "127.0.0.1:8000",
)


def check(root: Path) -> dict:
    if not (root / "index.html").is_file():
        raise ValueError("Static artifact has no index.html.")
    snapshot_path = root / "data" / "portfolio-demo.json"
    if not snapshot_path.is_file():
        raise ValueError("Static artifact has no verified portfolio snapshot.")

    files = [path for path in root.rglob("*") if path.is_file()]
    forbidden_files = [
        str(path.relative_to(root))
        for path in files
        if path.suffix.lower() in FORBIDDEN_SUFFIXES
    ]
    if forbidden_files:
        raise ValueError(f"Forbidden deployable files: {forbidden_files}")

    exposed = []
    external_calls = []
    searchable_text = []
    for path in files:
        if path.suffix.lower() not in {".html", ".js", ".css", ".json", ".txt"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        searchable_text.append(text)
        for fragment in FORBIDDEN_TEXT:
            if fragment in text:
                exposed.append((str(path.relative_to(root)), fragment))
        if "fetch(\"http" in text or "fetch('http" in text:
            external_calls.append(str(path.relative_to(root)))
    if exposed:
        raise ValueError(f"Sensitive or backend-only text in deployable artifact: {exposed}")
    if external_calls:
        raise ValueError(f"External fetch found in deployable artifact: {external_calls}")
    combined = "\n".join(searchable_text)
    required_public_text = (
        "Verified historical snapshot",
        "https://doi.org/10.24432/C5CG6D",
        "https://creativecommons.org/licenses/by/4.0/",
    )
    missing_public_text = [text for text in required_public_text if text not in combined]
    if missing_public_text:
        raise ValueError(f"Required public attribution is missing: {missing_public_text}")

    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    core = {
        key: snapshot[key]
        for key in ("metadata", "filtered", "fixed", "opportunities")
    }
    fingerprint = hashlib.sha256(
        json.dumps(core, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    if fingerprint != snapshot.get("analytical_fingerprint_sha256"):
        raise ValueError("Deployable snapshot fingerprint mismatch.")

    return {
        "files": len(files),
        "bytes": sum(path.stat().st_size for path in files),
        "snapshot_bytes": snapshot_path.stat().st_size,
        "fingerprint": fingerprint,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path, nargs="?", default=Path("web/dist"))
    args = parser.parse_args()
    print(json.dumps(check(args.root), sort_keys=True))


if __name__ == "__main__":
    main()
