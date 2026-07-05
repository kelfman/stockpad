"""
RRG-style relative-strength signals for all 11 GICS sector ETFs vs SPY.

Reconstructs the JdK RS-Ratio / RS-Momentum idea from Relative Rotation Graphs
(Julius de Kempenaer). RRG Research has never published the exact proprietary
formula, so this is a well-known community approximation -- same idea, not a
byte-identical match to a Bloomberg/StockCharts RRG chart.

The unit of output is the turn, not the position: each sector gets a quadrant,
how long it has been there, and which way it is heading. A turn is only called
after CONFIRM_WEEKS consecutive weeks -- a single week near a boundary is
noise, and both axes are rolling z-scores that will flicker there.

Run: python scripts/sector_rotation.py
Writes the full weekly series to data/sector_rotation.json -- history is the
point; the dashboard's time-scrubbing needs it accumulating from day one.
"""

import json
import os
import time
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

POLYGON_API_KEY = os.environ["POLYGON_API_KEY"]

SECTORS = {
    "XLB": "Materials",
    "XLC": "Communication Services",
    "XLE": "Energy",
    "XLF": "Financials",
    "XLI": "Industrials",
    "XLK": "Technology",
    "XLP": "Consumer Staples",
    "XLRE": "Real Estate",
    "XLU": "Utilities",
    "XLV": "Health Care",
    "XLY": "Consumer Discretionary",
}
BENCHMARK = "SPY"
LOOKBACK_DAYS = 400  # comfortably over a year of daily bars once resampled to weekly
SMOOTH_WINDOW = 14  # weeks -- EMA span applied to the raw ratio
NORM_WINDOW = 14  # weeks -- rolling window used to z-score-normalize around 100
MOMENTUM_LOOKBACK = 4  # weeks -- rate-of-change window for the momentum axis
CONFIRM_WEEKS = 3  # consecutive weeks required before a turn is called
HEADING_LOOKBACK = 4  # weeks used to judge which way a sector is travelling

MAX_RETRIES = 6

OUT_PATH = Path(__file__).resolve().parent.parent / "data" / "sector_rotation.json"


def fetch_daily_closes(ticker: str) -> pd.Series:
    end = date.today()
    start = end - timedelta(days=LOOKBACK_DAYS)
    url = (
        f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/day/"
        f"{start.isoformat()}/{end.isoformat()}"
    )
    delay = 5
    for _ in range(MAX_RETRIES):
        resp = requests.get(
            url,
            params={"adjusted": "true", "sort": "asc", "limit": 5000, "apiKey": POLYGON_API_KEY},
            timeout=30,
        )
        if resp.status_code == 429:
            time.sleep(int(resp.headers.get("Retry-After", delay)))
            delay *= 2
            continue
        resp.raise_for_status()
        payload = resp.json()
        if payload.get("resultsCount", 0) == 0:
            raise RuntimeError(f"Polygon returned no bars for {ticker}: {payload}")
        df = pd.DataFrame(payload["results"])
        df["date"] = pd.to_datetime(df["t"], unit="ms")
        return df.set_index("date")["c"].rename(ticker)
    raise RuntimeError(f"Polygon rate limit not cleared after {MAX_RETRIES} retries for {ticker}")


def to_weekly(series: pd.Series) -> pd.Series:
    weekly = series.resample("W-FRI").last().dropna()
    # Mid-week runs produce a partial bar labelled with the coming Friday --
    # noise for a turn detector, so drop it.
    if weekly.index[-1].date() > date.today():
        weekly = weekly.iloc[:-1]
    return weekly


def zscore_normalize(series: pd.Series, window: int) -> pd.Series:
    rolling_mean = series.rolling(window).mean()
    rolling_std = series.rolling(window).std()
    return 100 + 10 * (series - rolling_mean) / rolling_std


def rrg_track(sector_close: pd.Series, benchmark_close: pd.Series) -> pd.DataFrame:
    rs = (sector_close / benchmark_close).dropna()
    rs_smoothed = rs.ewm(span=SMOOTH_WINDOW, adjust=False).mean()
    rs_ratio = zscore_normalize(rs_smoothed, NORM_WINDOW)
    rs_momentum = zscore_normalize(rs_ratio.diff(MOMENTUM_LOOKBACK), NORM_WINDOW)
    return pd.DataFrame({"rs_ratio": rs_ratio, "rs_momentum": rs_momentum}).dropna()


def quadrant_of(rs_ratio: float, rs_momentum: float) -> str:
    if rs_ratio > 100:
        return "Leading" if rs_momentum > 100 else "Weakening"
    return "Improving" if rs_momentum > 100 else "Lagging"


def weeks_in_quadrant(track: pd.DataFrame) -> int:
    quads = [quadrant_of(r, m) for r, m in zip(track["rs_ratio"], track["rs_momentum"])]
    current, count = quads[-1], 0
    for q in reversed(quads):
        if q != current:
            break
        count += 1
    return count


def consecutive_rising(series: pd.Series) -> int:
    count = 0
    for delta in reversed(series.diff().dropna().tolist()):
        if delta <= 0:
            break
        count += 1
    return count


def heading_of(track: pd.DataFrame) -> str:
    """Linear extrapolation of the last HEADING_LOOKBACK weeks of travel."""
    r_now = track["rs_ratio"].iloc[-1]
    m_now = track["rs_momentum"].iloc[-1]
    r_past = track["rs_ratio"].iloc[-1 - HEADING_LOOKBACK]
    m_past = track["rs_momentum"].iloc[-1 - HEADING_LOOKBACK]
    projected = quadrant_of(r_now + (r_now - r_past), m_now + (m_now - m_past))
    current = quadrant_of(r_now, m_now)
    return "holding" if projected == current else f"toward {projected}"


def momentum_percentile(track: pd.DataFrame) -> int:
    """Where the latest RS-Momentum sits within this sector's own track history."""
    momentum = track["rs_momentum"]
    return int(round(float((momentum <= momentum.iloc[-1]).mean() * 100)))


def classify(track: pd.DataFrame) -> dict:
    """Turn-aware read: the trajectory carries the meaning, not the position.

    A one-point quadrant snapshot misreads the two most interesting moments --
    a laggard curling upward (early turn, not "strong bearish") and a leader
    losing momentum (caution, not yet bearish). `confirmed` means the state or
    turn has persisted CONFIRM_WEEKS; interpretation lives in the reading text.
    """
    quadrant = quadrant_of(track["rs_ratio"].iloc[-1], track["rs_momentum"].iloc[-1])
    weeks_in = weeks_in_quadrant(track)
    ratio_rising = consecutive_rising(track["rs_ratio"])
    momentum_rising = consecutive_rising(track["rs_momentum"])

    if quadrant == "Leading":
        if weeks_in >= CONFIRM_WEEKS:
            return {
                "direction": "bullish",
                "confirmed": True,
                "reading": f"established leadership, {weeks_in} consecutive weeks in Leading",
            }
        return {
            "direction": "bullish",
            "confirmed": False,
            "reading": (
                f"newly into Leading ({weeks_in} wk) -- "
                f"below the {CONFIRM_WEEKS}-week confirmation bar"
            ),
        }
    if quadrant == "Weakening":
        return {
            "direction": "neutral",
            "confirmed": weeks_in >= CONFIRM_WEEKS,
            "reading": (
                f"still outperforming but momentum fading, {weeks_in} wk in Weakening -- "
                "watch for recovery or rollover into Lagging"
            ),
        }
    if quadrant == "Improving":
        if ratio_rising >= CONFIRM_WEEKS:
            return {
                "direction": "bullish",
                "confirmed": True,
                "reading": (
                    f"ratio bottomed and curled upward {ratio_rising} consecutive weeks -- "
                    "confirmed early rotation, not yet outperforming"
                ),
            }
        return {
            "direction": "neutral",
            "confirmed": False,
            "reading": (
                f"possible turn ({weeks_in} wk in Improving) but the ratio rise is "
                f"unconfirmed -- {ratio_rising} wk rising, needs {CONFIRM_WEEKS} consecutive"
            ),
        }
    if momentum_rising >= CONFIRM_WEEKS:
        return {
            "direction": "bullish",
            "confirmed": False,
            "reading": (
                f"laggard with momentum curling up {momentum_rising} consecutive weeks -- "
                "classic early-turn watch, unconfirmed until it reaches Improving"
            ),
        }
    return {
        "direction": "bearish",
        "confirmed": weeks_in >= CONFIRM_WEEKS,
        "reading": f"entrenched laggard, {weeks_in} wk in Lagging with no sign of a turn",
    }


def build_sector(ticker: str, benchmark_close: pd.Series) -> dict:
    track = rrg_track(to_weekly(fetch_daily_closes(ticker)), benchmark_close)

    latest = track.iloc[-1]
    quadrant = quadrant_of(latest["rs_ratio"], latest["rs_momentum"])
    read = classify(track)
    heading = heading_of(track)
    percentile = momentum_percentile(track)
    as_of = track.index[-1].date().isoformat()

    signal = {
        "subject_type": "sector",
        "subject": ticker,
        "source": "relative_strength_ratio",
        "direction": read["direction"],
        "percentile_vs_history": percentile,
        "confirmed": read["confirmed"],
        "descriptor": (
            f"{ticker} ({SECTORS[ticker]}): {read['reading']} "
            f"(RS-Ratio {latest['rs_ratio']:.1f}, RS-Momentum {latest['rs_momentum']:.1f} "
            f"at p{percentile} of trailing {len(track)} wks, heading {heading})"
        ),
        "as_of": as_of,
        "staleness": "fresh",
    }

    return {
        "ticker": ticker,
        "name": SECTORS[ticker],
        "quadrant": quadrant,
        "weeks_in_quadrant": weeks_in_quadrant(track),
        "heading": heading,
        "rs_ratio": round(float(latest["rs_ratio"]), 2),
        "rs_momentum": round(float(latest["rs_momentum"]), 2),
        "momentum_percentile": percentile,
        "signal": signal,
        "series": [
            {
                "date": idx.date().isoformat(),
                "rs_ratio": round(float(row["rs_ratio"]), 2),
                "rs_momentum": round(float(row["rs_momentum"]), 2),
                "quadrant": quadrant_of(row["rs_ratio"], row["rs_momentum"]),
            }
            for idx, row in track.iterrows()
        ],
    }


def main() -> None:
    benchmark_close = to_weekly(fetch_daily_closes(BENCHMARK))

    sectors = []
    for ticker in SECTORS:
        sectors.append(build_sector(ticker, benchmark_close))
        print(f"fetched {ticker}", flush=True)

    quadrant_order = {"Leading": 0, "Improving": 1, "Weakening": 2, "Lagging": 3}
    sectors.sort(key=lambda s: (quadrant_order[s["quadrant"]], -s["rs_momentum"]))

    as_of = sectors[0]["signal"]["as_of"]
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
                "sectors": sectors,
            },
            indent=2,
        )
    )

    print(f"\nSector rotation vs {BENCHMARK} -- as of {as_of}\n")
    header = (
        f"{'Sector':<7}{'Name':<24}{'Quadrant':<11}{'Wks':>4}  "
        f"{'Heading':<17}{'RS-Ratio':>9}{'RS-Mom':>8}{'Pctl':>6}  {'Conf'}"
    )
    print(header)
    print("-" * len(header))
    for s in sectors:
        conf = "yes" if s["signal"]["confirmed"] else "--"
        print(
            f"{s['ticker']:<7}{s['name']:<24}{s['quadrant']:<11}{s['weeks_in_quadrant']:>4}  "
            f"{s['heading']:<17}{s['rs_ratio']:>9.1f}{s['rs_momentum']:>8.1f}"
            f"{s['momentum_percentile']:>6}  {conf}"
        )

    print("\nSignals:")
    for s in sectors:
        sig = s["signal"]
        state = "confirmed" if sig["confirmed"] else "unconfirmed"
        print(f"  [{sig['direction']} · {state} · p{sig['percentile_vs_history']}] {sig['descriptor']}")

    print(f"\nFull weekly series written to {OUT_PATH.relative_to(Path.cwd())}")


if __name__ == "__main__":
    main()
