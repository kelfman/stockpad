"""Thin runner: fetch Form 4s -> compute insider cluster signals -> persist -> print.

Run: python scripts/run_insider_cluster.py
"""

import dataclasses
import json
from pathlib import Path

from connectors.edgar import fetch_all
from core.watchlist import WATCHLIST
from dashboard.watchlist import render
from signals.insider_cluster import BACKFILL_DAYS, build_ticker_signal

OUT_PATH = Path(__file__).resolve().parent.parent / "data" / "insider_cluster.json"
SECTOR_DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "sector_rotation.json"


def load_sector_lookup() -> dict:
    if not SECTOR_DATA_PATH.exists():
        return {}
    data = json.loads(SECTOR_DATA_PATH.read_text())
    return {s["ticker"]: s for s in data["sectors"]}


def to_json_dict(tickers: list[dict]) -> list[dict]:
    return [{**t, "signal": dataclasses.asdict(t["signal"])} for t in tickers]


def main() -> None:
    tickers = list(WATCHLIST)
    filings = fetch_all(tickers, lookback_days=BACKFILL_DAYS)

    results = []
    for ticker in tickers:
        result = build_ticker_signal(ticker, filings[ticker])
        result["sector_etf"] = WATCHLIST[ticker]
        results.append(result)

    OUT_PATH.parent.mkdir(exist_ok=True)
    OUT_PATH.write_text(json.dumps(to_json_dict(results), indent=2))

    sector_lookup = load_sector_lookup()
    print()
    print(render(results, sector_lookup))
    print(f"\nWritten to {OUT_PATH.relative_to(Path.cwd())}")


if __name__ == "__main__":
    main()
