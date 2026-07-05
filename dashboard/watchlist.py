"""Ticker watchlist view: insider cluster signals alongside sector context.

Basic form per Slice 2 -- a table, same spirit as the sector ranked table.
No percentile column: the insider signal is a sparse count with no honest
percentile, so the table shows the measured facts (buys in the window, how
long since the last one) instead of a fabricated one.
"""


def _last_buy(days: int | None) -> str:
    return "never" if days is None else f"{days}d ago"


def render(tickers: list[dict], sector_lookup: dict) -> str:
    lines = ["Insider cluster-buy watchlist", ""]

    header = (
        f"{'Ticker':<7}{'Sector':<7}{'Buys/12d':>9}  {'Last buy':>10}  "
        f"{'Conf':<6}Sector context"
    )
    lines.append(header)
    lines.append("-" * len(header))
    for t in tickers:
        sig = t["signal"]
        conf = "yes" if sig.confirmed else "--"
        sector_etf = t["sector_etf"]
        sector = sector_lookup.get(sector_etf)
        if sector:
            sector_sig = sector["signal"]
            note = f"{sector_etf} {sector['quadrant']} ({sector_sig['staleness']})"
        else:
            note = f"{sector_etf} (no sector data)"
        lines.append(
            f"{t['ticker']:<7}{sector_etf:<7}{t['latest_count']:>9}  "
            f"{_last_buy(t['days_since_last_buy']):>10}  {conf:<6}{note}"
        )

    lines.append("")
    lines.append("Signals:")
    for t in tickers:
        sig = t["signal"]
        state = "confirmed" if sig.confirmed else "unconfirmed"
        lines.append(f"  [{sig.direction} · {state} · {sig.staleness}] {sig.descriptor}")

    return "\n".join(lines)
