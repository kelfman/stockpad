"""RRG-style relative-strength signals for all 11 GICS sector ETFs vs SPY.

Reconstructs the JdK RS-Ratio / RS-Momentum idea from Relative Rotation Graphs
(Julius de Kempenaer). RRG Research has never published the exact proprietary
formula, so this is a well-known community approximation -- same idea, not a
byte-identical match to a Bloomberg/StockCharts RRG chart.

The unit of output is the turn, not the position: each sector gets a quadrant,
how long it has been there, and which way it is heading. A turn is only called
after CONFIRM_WEEKS consecutive weeks -- a single week near a boundary is
noise, and both axes are rolling z-scores that will flicker there.
"""

from datetime import date

import pandas as pd

from core.sectors import SECTORS
from core.staleness import staleness
from core.types import Direction, RawObservation, Signal, SubjectType

SMOOTH_WINDOW = 14  # weeks -- EMA span applied to the raw ratio
NORM_WINDOW = 14  # weeks -- rolling window used to z-score-normalize around 100
MOMENTUM_LOOKBACK = 4  # weeks -- rate-of-change window for the momentum axis
CONFIRM_WEEKS = 3  # consecutive weeks required before a turn is called
HEADING_LOOKBACK = 4  # weeks used to judge which way a sector is travelling
CADENCE_DAYS = 7  # weekly bars -- a reading older than a week means the run is stale


def normalise(observation: RawObservation) -> pd.Series:
    """Turn a raw Polygon bars payload into a daily close-price series."""
    df = pd.DataFrame(observation.payload["results"])
    df["date"] = pd.to_datetime(df["t"], unit="ms")
    return df.set_index("date")["c"].rename(observation.ticker)


def to_weekly(series: pd.Series) -> pd.Series:
    weekly = series.resample("W-FRI").last().dropna()
    # A mid-week run produces a partial bar labelled with the coming Friday --
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
                "direction": Direction.BULLISH,
                "confirmed": True,
                "reading": f"established leadership, {weeks_in} consecutive weeks in Leading",
            }
        return {
            "direction": Direction.BULLISH,
            "confirmed": False,
            "reading": (
                f"newly into Leading ({weeks_in} wk) -- "
                f"below the {CONFIRM_WEEKS}-week confirmation bar"
            ),
        }
    if quadrant == "Weakening":
        return {
            "direction": Direction.NEUTRAL,
            "confirmed": weeks_in >= CONFIRM_WEEKS,
            "reading": (
                f"still outperforming but momentum fading, {weeks_in} wk in Weakening -- "
                "watch for recovery or rollover into Lagging"
            ),
        }
    if quadrant == "Improving":
        if ratio_rising >= CONFIRM_WEEKS:
            return {
                "direction": Direction.BULLISH,
                "confirmed": True,
                "reading": (
                    f"ratio bottomed and curled upward {ratio_rising} consecutive weeks -- "
                    "confirmed early rotation, not yet outperforming"
                ),
            }
        return {
            "direction": Direction.NEUTRAL,
            "confirmed": False,
            "reading": (
                f"possible turn ({weeks_in} wk in Improving) but the ratio rise is "
                f"unconfirmed -- {ratio_rising} wk rising, needs {CONFIRM_WEEKS} consecutive"
            ),
        }
    if momentum_rising >= CONFIRM_WEEKS:
        return {
            "direction": Direction.BULLISH,
            "confirmed": False,
            "reading": (
                f"laggard with momentum curling up {momentum_rising} consecutive weeks -- "
                "classic early-turn watch, unconfirmed until it reaches Improving"
            ),
        }
    return {
        "direction": Direction.BEARISH,
        "confirmed": weeks_in >= CONFIRM_WEEKS,
        "reading": f"entrenched laggard, {weeks_in} wk in Lagging with no sign of a turn",
    }


def build_sector(ticker: str, observation: RawObservation, benchmark_weekly: pd.Series) -> dict:
    track = rrg_track(to_weekly(normalise(observation)), benchmark_weekly)

    latest = track.iloc[-1]
    quadrant = quadrant_of(latest["rs_ratio"], latest["rs_momentum"])
    read = classify(track)
    heading = heading_of(track)
    percentile = momentum_percentile(track)
    as_of = track.index[-1].date().isoformat()

    signal = Signal(
        subject_type=SubjectType.SECTOR,
        subject=ticker,
        source="relative_strength_ratio",
        direction=read["direction"],
        percentile_vs_history=percentile,
        confirmed=read["confirmed"],
        descriptor=(
            f"{ticker} ({SECTORS[ticker]}): {read['reading']} "
            f"(RS-Ratio {latest['rs_ratio']:.1f}, RS-Momentum {latest['rs_momentum']:.1f} "
            f"at p{percentile} of trailing {len(track)} wks, heading {heading})"
        ),
        as_of=as_of,
        staleness=staleness(as_of, CADENCE_DAYS),
    )

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
