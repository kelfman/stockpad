"""Computed freshness for a Signal -- never a hardcoded literal.

The rule ARCHITECTURE.md sets: a 90-day-stale 13F signal must never get
narrated with the same confidence as a same-day print. That only holds if
staleness is derived from the reading's actual age, so when a genuinely
lagged source lands it reports old instead of quietly claiming "fresh".

`cadence_days` is the source's own natural refresh horizon -- a weekly series
is fresh for a week, a quarterly 13F for a quarter. Anything older reports its
age in days rather than a bucket label, so no interpretive threshold is
invented beyond "within one cadence period or not".
"""

from datetime import date


def staleness(as_of: str, cadence_days: int) -> str:
    age = (date.today() - date.fromisoformat(as_of)).days
    if age <= cadence_days:
        return "fresh"
    return f"{age}d old"
