"""Insider cluster-buy signal from SEC Form 4 filings.

The heuristic: how many distinct insiders made an open-market purchase
(transaction code "P") within a trailing window. This is a sparse count, not
a continuous series -- for a name at its perpetual zero, a "percentile" is a
tie-splitting artifact (~p50) that looks like a middling measurement while
conveying nothing. So this signal reports no percentile; the honesty lives in
the measured facts surfaced in the descriptor -- buys vs the cluster
threshold, how long since the last one, how many across the backfill window --
per the README's "precise about what was measured" discipline.

Form 4 must be filed within ~2 business days of the trade, so the data is
near-real-time; the trailing window ends today, so the reading is genuinely
fresh. The age of the last actual buy (which may be old) is stated in words.
"""

from datetime import date, timedelta
from xml.etree import ElementTree

from core.staleness import staleness
from core.types import Direction, RawObservation, Signal, SubjectType

CLUSTER_WINDOW_DAYS = 12  # matches the "3 insiders, 12 days" example in README/ARCHITECTURE
CLUSTER_CONFIRM_INSIDERS = 3
BACKFILL_DAYS = 730  # ~2 years, enough to cover the "first cluster buy in 18 months" example
CADENCE_DAYS = 7  # window ends today, so the reading refreshes at least weekly


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


def purchases(transactions: list[dict]) -> list[tuple[date, str]]:
    """(date, owner) for every open-market purchase (transaction code "P")."""
    return [
        (date.fromisoformat(t["transaction_date"]), t["owner"])
        for t in transactions
        if t["transaction_code"] == "P"
    ]


def _facts(days_since_last_buy: int | None, total_purchases: int) -> str:
    years = BACKFILL_DAYS // 365
    if total_purchases == 0:
        return f"no open-market buys in the trailing {years} yrs"
    return (
        f"last open-market buy {days_since_last_buy}d ago; "
        f"{total_purchases} in the trailing {years} yrs"
    )


def classify(latest_count: int, days_since_last_buy: int | None, total_purchases: int) -> dict:
    facts = _facts(days_since_last_buy, total_purchases)
    if latest_count >= CLUSTER_CONFIRM_INSIDERS:
        return {
            "direction": Direction.BULLISH,
            "confirmed": True,
            "reading": (
                f"{latest_count} distinct insiders bought in the trailing "
                f"{CLUSTER_WINDOW_DAYS} days -- confirmed cluster buy ({facts})"
            ),
        }
    if latest_count > 0:
        return {
            "direction": Direction.NEUTRAL,
            "confirmed": False,
            "reading": (
                f"{latest_count} insider bought in the trailing {CLUSTER_WINDOW_DAYS} days -- "
                f"below the {CLUSTER_CONFIRM_INSIDERS}-insider cluster bar ({facts})"
            ),
        }
    return {
        "direction": Direction.NEUTRAL,
        "confirmed": False,
        "reading": f"no insider purchases in the trailing {CLUSTER_WINDOW_DAYS} days ({facts})",
    }


def build_ticker_signal(ticker: str, filings: list[RawObservation]) -> dict:
    transactions = [txn for obs in filings for txn in normalise(obs)]
    buys = purchases(transactions)

    today = date.today()
    window_start = today - timedelta(days=CLUSTER_WINDOW_DAYS)
    latest_count = len({owner for d, owner in buys if window_start < d <= today})
    total_purchases = len(buys)
    days_since_last_buy = (today - max(d for d, _ in buys)).days if buys else None

    read = classify(latest_count, days_since_last_buy, total_purchases)
    as_of = today.isoformat()

    signal = Signal(
        subject_type=SubjectType.TICKER,
        subject=ticker,
        source="insider_form4_cluster",
        direction=read["direction"],
        # A sparse count has no honest percentile -- the measured facts are in
        # the descriptor instead. See module docstring.
        percentile_vs_history=None,
        confirmed=read["confirmed"],
        descriptor=f"{ticker}: {read['reading']}",
        as_of=as_of,
        staleness=staleness(as_of, CADENCE_DAYS),
    )

    return {
        "ticker": ticker,
        "latest_count": latest_count,
        "days_since_last_buy": days_since_last_buy,
        "total_purchases": total_purchases,
        "signal": signal,
    }
