"""Download the UCI Online Retail II archive and verify its checksums.

The raw files are written to data/raw/ (git-ignored) and are never modified.
"""

from __future__ import annotations

import hashlib
import shutil
import urllib.request
import zipfile
from pathlib import Path

from commercial_intelligence.common.log_utils import get_logger, kv

log = get_logger(__name__)


class ChecksumError(RuntimeError):
    """Raised when a downloaded file does not match its pinned SHA-256."""


def sha256_of(path: Path, chunk_size: int = 1 << 20) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def verify_checksum(path: Path, expected: str) -> None:
    actual = sha256_of(path)
    if actual != expected.lower():
        raise ChecksumError(
            f"{path.name}: expected sha256 {expected}, got {actual}. "
            "The source file has changed; inspect it before updating config/settings.toml."
        )
    log.info(kv("checksum_ok", file=path.name, sha256=actual[:12]))


def download_file(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    log.info(kv("download_start", url=url))
    request = urllib.request.Request(url, headers={"User-Agent": "commercial-intelligence/0.1"})
    with urllib.request.urlopen(request, timeout=120) as response, tmp.open("wb") as out:
        shutil.copyfileobj(response, out)
    tmp.replace(dest)
    log.info(kv("download_done", file=dest.name, bytes=dest.stat().st_size))


def extract_member(zip_path: Path, member: str, dest_dir: Path) -> Path:
    """Extract one named member only (no path traversal from archive names)."""
    with zipfile.ZipFile(zip_path) as zf:
        if member not in zf.namelist():
            raise FileNotFoundError(f"{member} not in {zip_path.name}: {zf.namelist()}")
        target = dest_dir / Path(member).name
        with zf.open(member) as src, target.open("wb") as out:
            shutil.copyfileobj(src, out)
    return target
