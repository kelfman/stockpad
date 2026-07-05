"""Thin runner: fetch -> compute -> persist -> print.

All the real logic lives in connectors, signals, and dashboard -- this just
wires them together.

Run: python scripts/run_sector_rotation.py
Writes the full weekly series to data/sector_rotation.json -- history is the
point; the dashboard's time-scrubbing needs it accumulating from day one.
"""

import dataclasses
import json
from pathlib import Path

from connectors.polygon import fetch_all
from core.sectors import BENCHMARK, SECTORS
from dashboard.table import render, sort_sectors
from signals.sector_rotation import (
    CONFIRM_WEEKS,
    MOMENTUM_LOOKBACK,
    NORM_WINDOW,
    SMOOTH_WINDOW,
    build_sector,
    normalise,
    to_weekly,
)

OUT_PATH = Path(__file__).resolve().parent.parent / "data" / "sector_rotation.json"


def to_json_dict(sectors: list[dict]) -> list[dict]:
    return [{**s, "signal": dataclasses.asdict(s["signal"])} for s in sectors]


def main() -> None:
    observations = fetch_all([BENCHMARK, *SECTORS])
    benchmark_weekly = to_weekly(normalise(observations[BENCHMARK]))

    sectors = [
        build_sector(ticker, observations[ticker], benchmark_weekly) for ticker in SECTORS
    ]
    sectors = sort_sectors(sectors)
    as_of = sectors[0]["signal"].as_of

    OUT_PATH.parent.mkdir(exist_ok=True)
    OUT_PATH.write_text(
        json.dumps(
            {
                "benchmark": BENCHMARK,
                "as_of": as_of,
                "params": {
                    "smooth_window": SMOOTH_WINDOW,
                    "norm_window": NORM_WINDOW,
                    "momentum_lookback": MOMENTUM_LOOKBACK,
                    "confirm_weeks": CONFIRM_WEEKS,
                },
                "sectors": to_json_dict(sectors),
            },
            indent=2,
        )
    )

    print()
    print(render(sectors, BENCHMARK, as_of))
    print(f"\nFull weekly series written to {OUT_PATH.relative_to(Path.cwd())}")


if __name__ == "__main__":
    main()
