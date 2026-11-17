"""Build the committed CI fixture: a ~5% sample of the landing Parquet.

Sampling is by invoice number, hashed deterministically, so whole invoices are
kept or dropped together and the fixture still contains cancellations, the
sheet overlap window and non-product codes. Run after scripts/download.py.
"""

from __future__ import annotations

import duckdb

from commercial_intelligence.common.config import load_settings, repo_path
from commercial_intelligence.common.log_utils import get_logger, kv

log = get_logger(__name__)


def main() -> None:
    settings = load_settings()
    landing = repo_path(settings["paths"]["landing_parquet"])
    fixture = repo_path(settings["paths"]["fixture_parquet"])
    share = float(settings["fixture"]["invoice_share"])
    fixture.parent.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect()
    con.execute(
        "create table landing as select * from read_parquet(?)", [str(landing)]
    )
    bucket = int(round(share * 10000))
    # Keep an invoice if a stable hash of its number falls in the sample bucket.
    # Because the same invoice number appears in both sheets within the overlap
    # window, hashing by invoice keeps BOTH copies together, so the sample still
    # contains complete overlap pairs for rule R01 to verify.
    # COPY cannot take prepared parameters, so the path and bucket are inlined;
    # both are internal values from config, not user input.
    con.execute(
        f"""
        copy (
            select * from landing
            where (hash(trim("Invoice")) % 10000) < {bucket}
        ) to '{fixture}' (format parquet)
        """
    )
    n = con.execute("select count(*) from read_parquet($p)", {"p": str(fixture)}).fetchone()[0]
    con.close()
    log.info(kv("fixture_written", file=str(fixture), rows=n))


if __name__ == "__main__":
    main()
