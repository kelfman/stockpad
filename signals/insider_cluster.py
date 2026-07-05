"""Insider cluster-buy signal from SEC Form 4 filings.

The heuristic: how many distinct insiders made an open-market purchase
(transaction code "P") within a trailing window, tracked on the same weekly
cadence as the sector RS-ratio series so today's reading can be honestly
ranked against this ticker's own history -- including all the quiet weeks
where nothing happened, not just the event days themselves. Sampling only
event days would bias the distribution toward looking busier than it is.
"""

from datetime import date
from xml.etree import ElementTree

import pandas as pd

from core.types import Direction, RawObservation, Signal, SubjectType

CLUSTER_WINDOW_DAYS = 12  # matches the "3 insiders, 12 days" example in README/ARCHITECTURE
CLUSTER_CONFIRM_INSIDERS = 3
BACKFILL_DAYS = 730  # ~2 years, enough to cover the "first cluster buy in 18 months" example


def normalise(observation: RawObservation) -> list[dict]:
    """Extract non-derivative transactions from a raw Form 4 XML payload."""
    root = ElementTree.fromstring(observation.payload)
    owner_el = root.find("reportingOwner/reportingOwnerId/rptOwnerName")
    owner = owner_el.text if owner_el is not None else "unknown"

    transactions = []
    for txn in root.findall("nonDerivativeTable/nonDerivativeTransaction"):
        code_el = txn.find("transactionCoding/transactionCode")
        date_el = txn.find("transactionDate/value")
        shares_el = txn.find("transactionAmounts/transactionShares/value")
        price_el = txn.find("transactionAmounts/transactionPricePerShare/value")
        if code_el is None or date_el is None:
            continue
        transactions.append(
            {
                "owner": owner,
                "transaction_code": code_el.text,
                "transaction_date": date_el.text,
                "shares": float(shares_el.text) if shares_el is not None else None,
                "price": float(price_el.text) if price_el is not None else None,
            }
        )
    return transactions


def rolling_purchaser_series(transactions: list[dict], backfill_days: int = BACKFILL_DAYS) -> pd.Series:
    """Weekly series of distinct insiders with an open-market purchase (code
    "P") in the trailing CLUSTER_WINDOW_DAYS, sampled every week over the
    backfill window.
    """
    purchases = [
        (pd.Timestamp(t["transaction_date"]), t["owner"])
        for t in transactions
        if t["transaction_code"] == "P"
    ]

    end = pd.Timestamp(date.today())
    start = end - pd.Timedelta(days=backfill_days)
    weeks = pd.date_range(start, end, freq="W-FRI")

    counts = []
    for week_end in weeks:
        window_start = week_end - pd.Timedelta(days=CLUSTER_WINDOW_DAYS)
        distinct_owners = {owner for txn_date, owner in purchases if window_start < txn_date <= week_end}
        counts.append(len(distinct_owners))

    return pd.Series(counts, index=weeks)


def percentile_rank(series: pd.Series, value: float) -> int:
    """Mean-rank percentile: ties split the difference instead of all
    inflating to p100. Matters here because the series is mostly repeated
    small integers (0, 1, 2...), unlike a continuous z-score -- a ticker
    with zero purchase activity all along would otherwise show today's zero
    as a (meaningless) p100 instead of the unremarkable p50 it actually is.
    """
    below = int((series < value).sum())
    equal = int((series == value).sum())
    return int(round((below + 0.5 * equal) / len(series) * 100))


def classify(latest_count: int) -> dict:
    if latest_count >= CLUSTER_CONFIRM_INSIDERS:
        return {
            "direction": Direction.BULLISH,
            "confirmed": True,
            "reading": (
                f"{latest_count} distinct insiders bought in the trailing "
                f"{CLUSTER_WINDOW_DAYS} days -- confirmed cluster buy"
            ),
        }
    if latest_count > 0:
        return {
            "direction": Direction.NEUTRAL,
            "confirmed": False,
            "reading": (
                f"{latest_count} insider(s) bought in the trailing {CLUSTER_WINDOW_DAYS} days -- "
                f"below the {CLUSTER_CONFIRM_INSIDERS}-insider cluster bar"
            ),
        }
    return {
        "direction": Direction.NEUTRAL,
        "confirmed": False,
        "reading": f"no insider purchases in the trailing {CLUSTER_WINDOW_DAYS} days",
    }


def build_ticker_signal(ticker: str, filings: list[RawObservation]) -> dict:
    transactions = [txn for obs in filings for txn in normalise(obs)]
    series = rolling_purchaser_series(transactions)

    latest_count = int(series.iloc[-1])
    percentile = percentile_rank(series, latest_count)
    read = classify(latest_count)
    as_of = series.index[-1].date().isoformat()

    signal = Signal(
        subject_type=SubjectType.TICKER,
        subject=ticker,
        source="insider_form4_cluster",
        direction=read["direction"],
        percentile_vs_history=percentile,
        confirmed=read["confirmed"],
        descriptor=f"{ticker}: {read['reading']} (p{percentile} of trailing {len(series)} wks)",
        as_of=as_of,
        staleness="fresh",
    )

    return {
        "ticker": ticker,
        "latest_count": latest_count,
        "percentile": percentile,
        "signal": signal,
        "series": [
            {"date": idx.date().isoformat(), "distinct_purchasers": int(v)}
            for idx, v in series.items()
        ],
    }
