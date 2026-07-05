"""Shared contract: the only object types every project passes between them.

`RawObservation` is what `connectors` emits -- deliberately dumb, no
interpretation. `Signal` is what `signals` emits -- the only object type
anything downstream (`synthesis`, `dashboard`) is allowed to consume.
"""

from dataclasses import dataclass
from enum import StrEnum


class Direction(StrEnum):
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


class SubjectType(StrEnum):
    SECTOR = "sector"
    TICKER = "ticker"


@dataclass(frozen=True)
class RawObservation:
    source: str
    ticker: str
    observed_at: str
    retrieved_at: str
    payload: object


@dataclass(frozen=True)
class Signal:
    subject_type: SubjectType
    subject: str
    source: str
    direction: Direction
    percentile_vs_history: int
    confirmed: bool
    descriptor: str
    as_of: str
    staleness: str
